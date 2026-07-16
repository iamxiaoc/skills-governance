#!/usr/bin/env python3
"""
修改 Helm Chart 中的 trace 相关配置：
1. 在 deployment.yaml 中添加 OTEL Agent 环境变量
2. 在 ConfigMap 中移除 corp-trace 配置项
3. 在 values.yaml 中添加 otel-collector 地址
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

# Chart 目录列表
CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

# 需要在 deployment.yaml 的 env 中添加的 OTEL 环境变量
OTEL_ENVS = [
    ('OTEL_EXPORTER_OTLP_ENDPOINT', '"http://otel-collector.observability.svc.cluster.local:4317"'),
    ('OTEL_SERVICE_NAME', '"{{ .Values.global.namespace }}-{{ .name }}"'),
    ('OTEL_TRACES_EXPORTER', '"otlp"'),
    ('OTEL_METRICS_EXPORTER', '"none"'),
]


def update_values_yaml(chart_dir: Path):
    """在 values.yaml 中添加 trace 配置块"""
    values_file = chart_dir / "values.yaml"
    if not values_file.exists():
        return False

    content = values_file.read_text(encoding="utf-8")

    # 如果已存在 trace 配置则跳过
    if "otelCollector" in content:
        print(f"  values.yaml 已存在 otel 配置: {chart_dir.name}")
        return False

    # 在文件末尾添加 trace 配置块
    trace_config = """

# OpenTelemetry 链路追踪配置（替换 corp-trace）
otelCollector:
  endpoint: "http://otel-collector.observability.svc.cluster.local:4317"
  enabled: true
"""

    content += trace_config
    values_file.write_text(content, encoding="utf-8")
    print(f"  添加 otel 配置: {values_file.relative_to(PROJECT_ROOT)}")
    return True


def update_deployment_yaml(chart_dir: Path):
    """在 deployment.yaml 中注入 OTEL 环境变量"""
    templates_dir = chart_dir / "templates"
    if not templates_dir.exists():
        return

    for deploy in templates_dir.glob("*-deployment.yaml"):
        content = deploy.read_text(encoding="utf-8")

        if "OTEL_EXPORTER" in content:
            print(f"  deployment 已存在 OTEL 配置: {deploy.name}")
            continue

        # 在 SPRING_PROFILES_ACTIVE 环境变量后添加 OTEL 环境变量
        otel_env_block = """
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector.observability.svc.cluster.local:4317"
        - name: OTEL_SERVICE_NAME
          value: "{{ .Values.global.namespace }}-{{ template "fullname" . }}"
        - name: OTEL_TRACES_EXPORTER
          value: "otlp"
        - name: OTEL_PROPAGATORS
          value: "tracecontext,baggage"
"""

        # 在 SPRING_PROFILES_ACTIVE 块后插入
        content = re.sub(
            r'(- name: SPRING_PROFILES_ACTIVE\s*\n\s*value: "[^"]*")',
            r'\1' + otel_env_block,
            content,
            count=1,
        )

        deploy.write_text(content, encoding="utf-8")
        print(f"  注入 OTEL 环境变量: {deploy.relative_to(PROJECT_ROOT)}")


def remove_corp_trace_from_configmaps(chart_dir: Path):
    """从 ConfigMap 中移除 corp-trace 相关配置"""
    templates_dir = chart_dir / "templates"
    if not templates_dir.exists():
        return

    for cm in templates_dir.glob("*-configmap.yaml"):
        content = cm.read_text(encoding="utf-8")

        # 移除 corp-trace 配置项（示例：application.xml 中的 <trace> 块）
        original = content
        content = re.sub(
            r'\s*<trace>[\s\S]*?</trace>\s*',
            '\n',
            content,
        )
        # 移除 trace-url 等属性
        content = re.sub(
            r'\s*<!-- corp-trace 配置 -->[\s\S]*?-->',
            '',
            content,
        )

        if content != original:
            cm.write_text(content, encoding="utf-8")
            print(f"  清理 corp-trace 配置: {cm.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Helm Chart 修改: corp-trace → OpenTelemetry")
    print("=" * 70)

    for chart_dir in CHART_DIRS:
        if not chart_dir.exists():
            continue
        print(f"\n[{chart_dir.name}]")
        update_values_yaml(chart_dir)
        update_deployment_yaml(chart_dir)
        remove_corp_trace_from_configmaps(chart_dir)

    print("\n⚠️  后续需人工检查：")
    print("  1. values.yaml 中 otelCollector.endpoint 是否指向正确环境")
    print("  2. deployment.yaml 中是否需要 init-container 加载 otel-agent")
    print("  3. ConfigMap 中是否还有残留的 corp-trace 配置")


if __name__ == "__main__":
    main()
