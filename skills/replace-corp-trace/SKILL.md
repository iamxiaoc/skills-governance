---
name: "replace-corp-trace"
description: "将 corp-trace 链路追踪二方件替换为 OpenTelemetry 开源方案。Invoke when user asks to replace corp-trace component or migrate tracing to OpenTelemetry."
---

# 替换 corp-trace 为 OpenTelemetry

## 职责范围
本 skill 专门负责将 `corp-trace` 二方件（com.corp.trace）替换为 OpenTelemetry 开源方案。不处理其他二方件。

## 替换映射

| corp-trace 原始 API | OpenTelemetry 替代 |
|---------------------|-------------------|
| `TraceUtils.generateTraceId()` | `Tracer.spanBuilder(...).startSpan()` 自动生成 |
| `TraceUtils.startTrace()` | `Span span = tracer.spanBuilder(name).startSpan()` |
| `TraceUtils.continueTrace(traceId, spanId)` | `Context.wrap()` + `Span.fromContext()` |
| `TraceUtils.endTrace()` | `span.end()` |
| `TraceUtils.getDuration()` | `span.getLatencyNanos()` |
| `TraceContext.getTraceId()` | `Span.current().getSpanContext().getTraceId()` |
| `TraceContext.getSpanId()` | `Span.current().getSpanContext().getSpanId()` |
| `TraceContext.setTraceId()` | 由 OpenTelemetry SDK 自动管理，不可手动设置 |
| `TraceContext.clear()` | `scope.close()`（try-with-resources）|

## 影响范围
- `base-dependency/dependency-public/pom.xml` — 移除 corp-trace 依赖声明，添加 opentelemetry-bom
- `base-framework/base-web/` — TraceFilter 等过滤器需改写
- `base-framework/base-middleware/` — 中间件 trace 上下文传递
- 所有微服务的 `pom.xml` — 移除 corp-trace 依赖
- 所有微服务中使用 TraceUtils/TraceContext 的 Java 文件

## 执行步骤
1. 运行 `scripts/maven_replace.py` — 修改 pom.xml 依赖声明
2. 运行 `scripts/java_replace.py` — 替换 Java 代码中的 API 调用
3. 运行 `scripts/helm_replace.py` — 修改 Helm Chart 中的 trace 相关配置
4. 人工检查 OpenTelemetry Agent 配置（需额外配置 otel-collector 地址）

## 约束
- 仅替换 corp-trace，不触碰其他二方件
- OpenTelemetry 版本由 base-dependency 统一管理
- 替换后需保留 traceId 的语义，确保日志中仍可通过 traceId 串联
