---
name: "modify-base-framework"
description: "修改 base-framework 中封装了二方件的方法，使其适配替换后的开源组件。Invoke when user asks to modify base-framework wrappers or adapt framework to replaced components."
---

# 修改 base-framework 基础框架

## 职责范围
本 skill 负责修改 `base-framework` 各子 module 中封装了二方件的方法，使其适配替换后的开源组件。这是一类"多维度"skill，处理整个基础框架的适配。

## 影响的 base-framework 子 module
- `base-common` — 通用工具类（可能包含 trace 上下文传递）
- `base-web` — Web 过滤器（TraceFilter、ConfigFilter）
- `base-middleware` — 中间件封装（ID 生成、配置客户端、监控上报）
- `base-crypto` — 加密工具（可能依赖 config-client 获取密钥）
- `base-security` — 安全框架（可能依赖 trace 传递用户身份）
- `base-spring` — Spring 扩展（自动配置）

## 适配映射

| base-framework 原始封装 | 适配后 |
|------------------------|--------|
| `base-web/TraceFilter` 使用 corp-trace | 使用 OpenTelemetry SDK |
| `base-middleware/IdGenService` 使用 corp-id-generator | 使用 Leaf |
| `base-middleware/ConfigService` 使用 corp-config-client | 使用 Spring Cloud Config |
| `base-middleware/MonitorService` 使用 corp-monitor | 使用 Micrometer |
| `base-crypto/CryptoService` 依赖 config-client 获取密钥 | 改为 @Value 注入 |

## 执行步骤
1. 运行 `scripts/scan_framework_wrappers.py` — 扫描 base-framework 中所有引用二方件的封装类
2. 运行 `scripts/update_base_web.py` — 修改 base-web
3. 运行 `scripts/update_base_middleware.py` — 修改 base-middleware
4. 运行 `scripts/update_base_crypto.py` — 修改 base-crypto

## 约束
- 修改后需保持 base-framework 对外 API 不变（微服务无感知）
- 如果无法保持 API 兼容，需输出"破坏性变更清单"
- base-framework 的 pom.xml 中依赖版本仍由 base-dependency 管理
