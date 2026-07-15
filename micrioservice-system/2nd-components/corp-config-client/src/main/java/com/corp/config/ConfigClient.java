package com.corp.config;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 配置中心客户端（二方件提供）
 * 支持动态配置获取和监听
 */
public class ConfigClient {

    private final String serverUrl;
    private final String appName;
    private final String env;
    private final Map<String, String> configCache = new ConcurrentHashMap<>();

    public ConfigClient(String serverUrl, String appName, String env) {
        this.serverUrl = serverUrl;
        this.appName = appName;
        this.env = env;
    }

    /**
     * 获取配置
     */
    public String getConfig(String key) {
        return configCache.get(key);
    }

    /**
     * 获取配置（带默认值）
     */
    public String getConfig(String key, String defaultValue) {
        return configCache.getOrDefault(key, defaultValue);
    }

    /**
     * 获取int类型配置
     */
    public int getIntConfig(String key, int defaultValue) {
        String value = configCache.get(key);
        return value != null ? Integer.parseInt(value) : defaultValue;
    }

    /**
     * 获取boolean类型配置
     */
    public boolean getBooleanConfig(String key, boolean defaultValue) {
        String value = configCache.get(key);
        return value != null ? Boolean.parseBoolean(value) : defaultValue;
    }

    /**
     * 刷新配置缓存
     */
    public void refresh() {
        // 简化版：实际应从配置中心拉取
    }

    /**
     * 注册配置变更监听器
     */
    public void addListener(String key, ConfigChangeListener listener) {
        // 简化版：实际应订阅配置中心
    }
}
