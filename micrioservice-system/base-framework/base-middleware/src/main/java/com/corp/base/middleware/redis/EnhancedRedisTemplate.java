package com.corp.base.middleware.redis;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * Enhanced {@link RedisTemplate} that ships with safe serializers and basic
 * cache-protection utilities (null guard, default TTL, anti-cache-penetration
 * placeholders).
 */
public class EnhancedRedisTemplate<K, V> extends RedisTemplate<K, V> {

    /** Default TTL applied when none is specified. */
    public static final Duration DEFAULT_TTL = Duration.ofMinutes(30);

    /** Marker cached for empty/penetration-protection results. */
    public static final String EMPTY_MARK = "__BASE_EMPTY__";

    private final Map<K, Long> nullCacheUntil = new ConcurrentHashMap<>();

    public EnhancedRedisTemplate() {
        configureSerializers();
    }

    public EnhancedRedisTemplate(RedisConnectionFactory connectionFactory) {
        setConnectionFactory(connectionFactory);
        configureSerializers();
        afterPropertiesSet();
    }

    private void configureSerializers() {
        StringRedisSerializer keySerializer = new StringRedisSerializer();

        ObjectMapper mapper = new ObjectMapper();
        mapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        mapper.activateDefaultTyping(LaissezFaireSubTypeValidator.instance,
                ObjectMapper.DefaultTyping.NON_FINAL);
        GenericJackson2JsonRedisSerializer valueSerializer =
                new GenericJackson2JsonRedisSerializer(mapper);

        setKeySerializer(keySerializer);
        setHashKeySerializer(keySerializer);
        setValueSerializer(valueSerializer);
        setHashValueSerializer(valueSerializer);
        // Use byte-array based serialization for keys when stored as hash keys
        setEnableTransactionSupport(false);
    }

    /**
     * Put a value with the framework default TTL.
     */
    public void put(K key, V value) {
        put(key, value, DEFAULT_TTL);
    }

    /**
     * Put a value with explicit TTL.
     */
    public void put(K key, V value, Duration ttl) {
        if (key == null || value == null) {
            return;
        }
        opsForValue().set(key, value, ttl.toMillis(), TimeUnit.MILLISECONDS);
        // Invalidate any prior null-protection marker.
        nullCacheUntil.remove(key);
    }

    /**
     * Get a value with cache-protection: returns {@code null} and avoids
     * hitting the backend for {@code penetrationWindow} when a previous miss
     * was recorded.
     */
    @SuppressWarnings("unchecked")
    public V getWithProtection(K key, Duration penetrationWindow) {
        if (key == null) {
            return null;
        }
        Object raw = opsForValue().get(key);
        if (EMPTY_MARK.equals(raw)) {
            // Penetration-protection placeholder.
            return null;
        }
        if (raw != null) {
            return (V) raw;
        }
        // Cache the miss so callers can short-circuit subsequent lookups.
        nullCacheUntil.put(key, System.currentTimeMillis() + penetrationWindow.toMillis());
        return null;
    }

    /**
     * Returns true if a recent cache miss is still within the protection
     * window, indicating the backend should not be queried.
     */
    public boolean isWithinPenetrationWindow(K key) {
        Long until = nullCacheUntil.get(key);
        return until != null && until > System.currentTimeMillis();
    }

    /**
     * Mark a key as a penetration-protection placeholder so subsequent reads
     * short-circuit.
     */
    public void markEmpty(K key, Duration ttl) {
        opsForValue().set(key, (V) EMPTY_MARK, ttl.toMillis(), TimeUnit.MILLISECONDS);
    }

    /**
     * Bulk delete keys.
     */
    public long deleteAll(Set<K> keys) {
        if (keys == null || keys.isEmpty()) {
            return 0L;
        }
        Long n = delete(keys);
        return n == null ? 0L : n;
    }

    /**
     * Force a refresh of a cached value: delete and re-put.
     */
    public void refresh(K key, V value, Duration ttl) {
        delete(key);
        put(key, value, ttl);
    }
}
