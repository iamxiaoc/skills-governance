---
name: "update-helm-configmap"
description: "修改 Helm Chart 中 ConfigMap 的配置文件内容，适配二方件替换后的配置项变更。Invoke when user asks to update ConfigMap content or migrate config files for replaced components."
---

# Helm Chart ConfigMap 配置改造

## 职责范围
本 skill 负责修改 Helm Chart 中 ConfigMap 的配置文件内容。当二方件被替换后，配置文件中相关的配置项（如 trace-server、monitor-server、config-center 等）需要同步更新。这是一类"多维度"skill，处理整个配置体系的适配。

## 处理范围
- `user-module/user-module-chart/templates/*-configmap.yaml`
- `order-module/order-module-chart/templates/*-configmap.yaml`
- `product-module/product-module-chart/templates/*-configmap.yaml`

## 处理规则
1. **移除旧配置项**：删除指向公司内部基础设施的配置（如 corp-trace-server、corp-config-center、corp-monitor-server）
2. **添加新配置项**：添加开源替代方案的配置（如 otel-collector、spring-cloud-config、prometheus）
3. **保持结构一致**：ConfigMap 仍以完整配置文件形式挂载，仅修改文件内容
4. **保留 values 引用**：环境差异化变量仍通过 `{{ .Values.xxx }}` 引用，不硬编码

## 配置项映射

| 旧配置项 | 新配置项 | 说明 |
|---------|---------|------|
| `<trace><server>corp-trace...` | `<otel><endpoint>otel-collector...` | 链路追踪 |
| `<config><center>corp-config...` | `<spring-cloud-config><uri>config-server...` | 配置中心 |
| `<monitor><server>corp-monitor...` | `<prometheus><enabled>true</prometheus>` | 监控 |
| `<id-generator><workerId>` | `<leaf><workerId>` | ID 生成器 |

## 执行步骤
1. 运行 `scripts/scan_config_items.py` — 扫描所有 ConfigMap 中的旧配置项
2. 运行 `scripts/update_configmap.py` — 替换配置项内容
3. 运行 `scripts/validate_values.py` — 检查 values.yaml 是否提供了新配置项的变量

## 约束
- 不修改 Chart.yaml 和 values.yaml 的结构（仅更新内容）
- ConfigMap 名称保持不变，避免影响 deployment 中的 volumeMounts
- 替换后的配置项需确保格式与原配置文件格式一致（XML/YAML）
