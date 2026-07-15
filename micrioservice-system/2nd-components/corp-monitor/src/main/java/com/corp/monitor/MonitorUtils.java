package com.corp.monitor;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 监控指标采集工具（二方件提供）
 * 提供计数器、计时器、Gauge等指标采集能力
 */
public class MonitorUtils {

    private static final Map<String, AtomicLong> COUNTERS = new ConcurrentHashMap<>();
    private static final Map<String, Long> GAUGES = new ConcurrentHashMap<>();
    private static final Map<String, Long> TIMERS = new ConcurrentHashMap<>();

    /**
     * 计数器递增
     */
    public static void increment(String metricName) {
        increment(metricName, 1);
    }

    /**
     * 计数器递增指定值
     */
    public static void increment(String metricName, long value) {
        COUNTERS.computeIfAbsent(metricName, k -> new AtomicLong(0)).addAndGet(value);
    }

    /**
     * 设置Gauge值
     */
    public static void setGauge(String metricName, long value) {
        GAUGES.put(metricName, value);
    }

    /**
     * 记录耗时
     */
    public static void recordTime(String metricName, long millis) {
        TIMERS.put(metricName, millis);
    }

    /**
     * 开始计时
     */
    public static long startTimer() {
        return System.currentTimeMillis();
    }

    /**
     * 结束计时并记录
     */
    public static long stopTimer(String metricName, long startTime) {
        long duration = System.currentTimeMillis() - startTime;
        recordTime(metricName, duration);
        return duration;
    }

    /**
     * 获取计数器值
     */
    public static long getCounter(String metricName) {
        AtomicLong counter = COUNTERS.get(metricName);
        return counter != null ? counter.get() : 0;
    }

    /**
     * 获取Gauge值
     */
    public static long getGauge(String metricName) {
        return GAUGES.getOrDefault(metricName, 0L);
    }
}
