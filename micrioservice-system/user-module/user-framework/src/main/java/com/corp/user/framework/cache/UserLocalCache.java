package com.corp.user.framework.cache;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 用户本地缓存
 * FIXME: 该工具类为通用能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：通用本地缓存工具被放在了业务模块的framework中
 * 基于ConcurrentHashMap的简单缓存，带有过期淘汰机制
 */
public class UserLocalCache<K, V> {

    private final Map<K, CacheEntry<V>> cache = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

    public UserLocalCache() {
        // 每分钟清理一次过期缓存
        scheduler.scheduleAtFixedRate(this::cleanExpired, 1, 1, TimeUnit.MINUTES);
    }

    public void put(K key, V value, long expireMillis) {
        cache.put(key, new CacheEntry<>(value, System.currentTimeMillis() + expireMillis));
    }

    public V get(K key) {
        CacheEntry<V> entry = cache.get(key);
        if (entry == null) {
            return null;
        }
        if (System.currentTimeMillis() > entry.expireTime) {
            cache.remove(key);
            return null;
        }
        return entry.value;
    }

    public void remove(K key) {
        cache.remove(key);
    }

    private void cleanExpired() {
        long now = System.currentTimeMillis();
        cache.entrySet().removeIf(entry -> now > entry.getValue().expireTime);
    }

    private static class CacheEntry<V> {
        final V value;
        final long expireTime;

        CacheEntry(V value, long expireTime) {
            this.value = value;
            this.expireTime = expireTime;
        }
    }
}
