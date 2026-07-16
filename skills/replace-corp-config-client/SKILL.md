---
name: "replace-corp-config-client"
description: "将 corp-config-client 配置中心客户端二方件替换为 Spring Cloud Config 开源方案。Invoke when user asks to replace corp-config-client or migrate config center client."
---

# 替换 corp-config-client 为 Spring Cloud Config

## 职责范围
本 skill 专门负责将 `corp-config-client` 二方件（com.corp.config）替换为 Spring Cloud Config 客户端。不处理其他二方件。

## 替换映射

| corp-config-client 原始 API | Spring Cloud Config 替代 |
|----------------------------|--------------------------|
| `new ConfigClient(url, app, env)` | 通过 `@RefreshScope` + `@Value` 自动注入 |
| `client.getConfig(key)` | `@Value("${key}")` 字段注入 |
| `client.getConfig(key, default)` | `@Value("${key:default}")` |
| `client.getIntConfig(key, def)` | `@Value("${key:def}")` int 字段 |
| `client.getBooleanConfig(key, def)` | `@Value("${key:def}")` boolean 字段 |
| `client.refresh()` | `POST /actuator/refresh` 或 `@RefreshScope` 自动刷新 |
| `client.addListener(key, listener)` | `@EventListener(RefreshScopeRefreshedEvent.class)` |
| `implements ConfigChangeListener` | `@EventListener` 方式 |

## 影响范围
- `base-dependency/dependency-public/pom.xml` — 移除 corp-config-client，添加 spring-cloud-config-client
- `base-framework/base-middleware/` — 配置客户端封装
- 所有微服务中使用 ConfigClient 的 Java 文件
- 所有微服务的 ConfigMap（需添加 spring.cloud.config 配置）

## 执行步骤
1. 运行 `scripts/maven_replace.py` — 修改 pom.xml
2. 运行 `scripts/java_replace.py` — 替换 Java 代码
3. 运行 `scripts/helm_replace.py` — 修改 ConfigMap，添加 spring.cloud.config

## 约束
- 仅替换 corp-config-client
- Spring Cloud Config 版本由 base-dependency 统一管理
- 需部署独立的 Config Server（helm 中需添加 ConfigMap 指向）
- 动态监听机制变化较大：从主动注册 listener 改为被动 @EventListener
