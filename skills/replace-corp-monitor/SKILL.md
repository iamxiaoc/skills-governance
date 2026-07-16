---
name: "replace-corp-monitor"
description: "将 corp-monitor 监控二方件替换为 Micrometer + Prometheus 开源方案。Invoke when user asks to replace corp-monitor or migrate monitoring to Micrometer."
---

# 替换 corp-monitor 为 Micrometer + Prometheus

## 职责范围
本 skill 专门负责将 `corp-monitor` 二方件（com.corp.monitor）替换为 Micrometer + Prometheus 开源方案。

## 替换映射

| corp-monitor 原始 API | Micrometer 替代 |
|----------------------|-----------------|
| `MonitorUtils.increment(name)` | `counter(name).increment()` |
| `MonitorUtils.increment(name, val)` | `counter(name).increment(val)` |
| `MonitorUtils.setGauge(name, val)` | `gauge(name, val)` |
| `MonitorUtils.recordTime(name, ms)` | `timer(name).record(ms, MS)` |
| `MonitorUtils.startTimer()` | `timer.start()` → `Sample` |
| `MonitorUtils.stopTimer(name, start)` | `sample.stop(registry)` |
| `MonitorUtils.getCounter(name)` | `counter(name).count()` |
| `new MonitorReporter(url, interval)` | `PrometheusMeterRegistry` + `/actuator/prometheus` |
| `reporter.start()` | Spring Boot Actuator 自动暴露 |
| `reporter.stop()` | 无需手动停止 |

## 影响范围
- `base-dependency/dependency-public/pom.xml` — 移除 corp-monitor，添加 micrometer-registry-prometheus
- `base-framework/base-middleware/` — MonitorUtils 封装需改写为 Micrometer
- 所有微服务中使用 MonitorUtils/MonitorReporter 的 Java 文件
- Helm Chart ConfigMap（移除 monitor-server 配置，添加 prometheus 配置）

## 执行步骤
1. 运行 `scripts/maven_replace.py`
2. 运行 `scripts/java_replace.py`
3. 运行 `scripts/helm_replace.py`

## 约束
- 仅替换 corp-monitor
- Micrometer 版本由 Spring Boot BOM 管理，无需在 base-dependency 单独声明版本
- 需要修改 deployment.yaml 添加 annotations: prometheus.io/scrape: "true"
