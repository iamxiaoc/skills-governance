package com.corp.id;

import java.util.concurrent.ConcurrentHashMap;

/**
 * ID生成器工厂（二方件提供）
 */
public class IdGeneratorFactory {

    private static final ConcurrentHashMap<String, IdGenerator> GENERATORS = new ConcurrentHashMap<>();

    /**
     * 获取默认ID生成器
     */
    public static IdGenerator getDefault() {
        return getOrCreate(1L, 1L);
    }

    /**
     * 获取或创建ID生成器
     */
    public static IdGenerator getOrCreate(long workerId, long datacenterId) {
        String key = workerId + "_" + datacenterId;
        return GENERATORS.computeIfAbsent(key, k -> new IdGenerator(workerId, datacenterId));
    }
}
