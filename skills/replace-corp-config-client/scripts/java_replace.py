#!/usr/bin/env python3
"""替换 Java 代码中 corp-config-client API 为 Spring Cloud Config"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

IMPORT_REPLACEMENTS = {
    "com.corp.config.ConfigClient": "org.springframework.beans.factory.annotation.Value",
    "com.corp.config.ConfigChangeListener": "org.springframework.cloud.context.config.annotation.RefreshScope",
}

# 方法调用替换（简化版，实际需人工调整）
CODE_REPLACEMENTS = [
    (re.compile(r"configClient\.getConfig\((\w+),\s*(\w+)\)"),
     r'/* TODO: 改为 @Value("${\1:\2}") */ null'),
    (re.compile(r"configClient\.getIntConfig\((\w+),\s*(\w+)\)"),
     r'/* TODO: 改为 @Value("${\1:\2}") */ \2'),
    (re.compile(r"configClient\.refresh\(\)"),
     '/* TODO: 通过 /actuator/refresh 触发 */'),
]


def replace_in_java(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content
    for old, new in IMPORT_REPLACEMENTS.items():
        content = content.replace(f"import {old};", f"import {new};")
    for pattern, replacement in CODE_REPLACEMENTS:
        content = pattern.sub(replacement, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"  已替换: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("Java 替换: corp-config-client → Spring Cloud Config")
    print("=" * 70)
    java_files = list(MICROSERVICE_DIR.rglob("*.java"))
    total = sum(1 for j in java_files if replace_in_java(j))
    print(f"\n共修改 {total} 个 Java 文件")
    print("\n⚠️  ConfigClient 改为 @Value 注入，需人工调整 Bean 初始化方式")


if __name__ == "__main__":
    main()
