#!/usr/bin/env python3
"""修改 Helm Chart：添加 prometheus 采集注解"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

PROMETHEUS_ANNOTATIONS = """        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus\""""


def update_deployment(chart_dir: Path):
    templates = chart_dir / "templates"
    if not templates.exists():
        return
    for deploy in templates.glob("*-deployment.yaml"):
        content = deploy.read_text(encoding="utf-8")
        if "prometheus.io/scrape" in content:
            print(f"  已存在 prometheus 注解: {deploy.name}")
            continue
        # 在 template metadata.annotations 中添加
        content = re.sub(
            r'(annotations:\s*\n(?:\s+[\w.-]+:[^\n]*\n)*?)(\s+spec:)',
            r'\1' + PROMETHEUS_ANNOTATIONS + '\n\2',
            content,
            count=1,
        )
        deploy.write_text(content, encoding="utf-8")
        print(f"  添加 prometheus 注解: {deploy.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Helm Chart 修改: 添加 Prometheus 采集配置")
    print("=" * 70)
    for chart_dir in CHART_DIRS:
        if chart_dir.exists():
            print(f"\n[{chart_dir.name}]")
            update_deployment(chart_dir)


if __name__ == "__main__":
    main()
