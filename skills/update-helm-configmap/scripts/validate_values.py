#!/usr/bin/env python3
"""检查 values.yaml 是否提供了新配置项的变量"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

REQUIRED_NEW_VARS = [
    ("otelCollector", "OpenTelemetry collector 地址"),
    ("configServer", "Spring Cloud Config Server 地址"),
]


def validate_values(values_file: Path):
    content = values_file.read_text(encoding="utf-8")
    missing = []
    for var_name, desc in REQUIRED_NEW_VARS:
        if var_name not in content:
            missing.append((var_name, desc))
    return missing


def main():
    print("=" * 70)
    print("验证 values.yaml 新变量")
    print("=" * 70)
    for chart_dir in CHART_DIRS:
        if not chart_dir.exists():
            continue
        values = chart_dir / "values.yaml"
        if not values.exists():
            continue
        print(f"\n[{chart_dir.name}]")
        missing = validate_values(values)
        if missing:
            for var_name, desc in missing:
                print(f"  ⚠️  缺少: {var_name} ({desc})")
        else:
            print(f"  ✅ 所有必要变量已存在")


if __name__ == "__main__":
    main()
