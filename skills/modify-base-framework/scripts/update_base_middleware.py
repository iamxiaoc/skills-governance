#!/usr/bin/env python3
"""修改 base-middleware：适配 Leaf / Spring Cloud Config / Micrometer"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASE_MW_DIR = PROJECT_ROOT / "micrioservice-system" / "base-framework" / "base-middleware"

IMPORT_REPLACEMENTS = {
    "com.corp.id.IdGenerator": "com.dept.leaf.LeafIDGen",
    "com.corp.id.IdGeneratorFactory": "com.dept.leaf.LeafIDGenFactory",
    "com.corp.config.ConfigClient": "org.springframework.beans.factory.annotation.Value",
    "com.corp.config.ConfigChangeListener": "org.springframework.cloud.context.config.annotation.RefreshScope",
    "com.corp.monitor.MonitorUtils": "io.micrometer.core.instrument.Metrics",
    "com.corp.monitor.MonitorReporter": "io.micrometer.core.instrument.MeterRegistry",
}


def update_java(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False
    original = content
    for old, new in IMPORT_REPLACEMENTS.items():
        content = content.replace(f"import {old};", f"import {new};")
    content = re.sub(r"\bIdGeneratorFactory\b", "LeafIDGenFactory", content)
    content = re.sub(r"\bIdGenerator\b", "LeafIDGen", content)
    content = re.sub(r"MonitorUtils\.increment\((\w+)\)", r'Metrics.counter("\1").increment()', content)
    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"  已更新: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("更新 base-middleware")
    print("=" * 70)
    if not BASE_MW_DIR.exists():
        print("base-middleware 目录不存在")
        return
    total = sum(1 for j in BASE_MW_DIR.rglob("*.java") if update_java(j))
    print(f"\n共修改 {total} 个 Java 文件")


if __name__ == "__main__":
    main()
