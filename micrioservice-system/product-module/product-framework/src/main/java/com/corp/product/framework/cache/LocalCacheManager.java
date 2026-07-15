package com.corp.product.framework.cache;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * 本地缓存管理器
 * FIXME: 该工具类为通用能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：通用缓存管理被放在了业务模块的framework中
 * 基于Caffeine的缓存管理（简化版用ConcurrentHashMap模拟）
 */
public class LocalCacheManager<K, V> {

    private final Map<K, V> cache = new ConcurrentHashMap<>();

    public void put(K key, V value) {
        cache.put(key, value);
    }

    public void put(K key, V value, long expire, TimeUnit timeUnit) {
        // 简化版：实际应使用Caffeine的expireAfterWrite
        cache.put(key, value);
    }

    public V get(K key) {
        return cache.get(key);
    }

    public V getOrDefault(K key, V defaultValue) {
        return cache.getOrDefault(key, defaultValue);
    }

    public void remove(K key) {
        cache.remove(key);
    }

    public void clear() {
        cache.clear();
    }

    public boolean containsKey(K key) {
        return cache.containsKey(key);
    }
}
