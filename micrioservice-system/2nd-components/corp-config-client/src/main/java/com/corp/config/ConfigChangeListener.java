package com.corp.config;

/**
 * 配置变更监听器（二方件提供）
 */
public interface ConfigChangeListener {
    void onChange(String key, String oldValue, String newValue);
}
