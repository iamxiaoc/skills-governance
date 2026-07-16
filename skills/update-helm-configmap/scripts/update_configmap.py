#!/usr/bin/env python3
"""替换 ConfigMap 中的旧配置项为新配置"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

REPLACEMENTS = [
    # trace
    (r"<trace>\s*<server>[^<]+</server>\s*</trace>",
     '<otel><endpoint>http://otel-collector.observability.svc.cluster.local:4317</endpoint></otel>'),
    # config-center
    (r"<config-center>[^<]+</config-center>",
     '<spring-cloud-config><uri>http://config-server.config-server.svc.cluster.local:8888</uri></spring-cloud-config>'),
    # monitor
    (r"<monitor>\s*<server>[^<]+</server>\s*</monitor>",
     '<prometheus><enabled>true</enabled></prometheus>'),
    # id-generator
    (r"<id-generator>",
     "<leaf>"),
    (r"</id-generator>",
     "</leaf>"),
]


def update_configmap(cm_path: Path):
    content = cm_path.read_text(encoding="utf-8")
    original = content
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    if content != original:
        cm_path.write_text(content, encoding="utf-8")
        print(f"  已更新: {cm_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("更新 ConfigMap 配置项")
    print("=" * 70)
    total = 0
    for chart_dir in CHART_DIRS:
        if not chart_dir.exists():
            continue
        templates = chart_dir / "templates"
        if not templates.exists():
            continue
        print(f"\n[{chart_dir.name}]")
        for cm in templates.glob("*-configmap.yaml"):
            if update_configmap(cm):
                total += 1
    print(f"\n共修改 {total} 个 ConfigMap")


if __name__ == "__main__":
    main()
