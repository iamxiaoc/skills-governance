package com.corp.monitor;

/**
 * 监控数据上报器（二方件提供）
 */
public class MonitorReporter {

    private final String endpoint;
    private final int intervalSeconds;

    public MonitorReporter(String endpoint, int intervalSeconds) {
        this.endpoint = endpoint;
        this.intervalSeconds = intervalSeconds;
    }

    /**
     * 启动定时上报
     */
    public void start() {
        // 简化版：实际应启动定时线程池上报到监控系统
    }

    /**
     * 手动上报一次
     */
    public void report() {
        // 简化版：实际应将MonitorUtils中的指标上报到监控系统
    }

    /**
     * 停止上报
     */
    public void stop() {
        // 简化版
    }
}
