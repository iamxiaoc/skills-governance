#!/usr/bin/env python3
"""修改 base-crypto：将依赖 corp-config-client 获取密钥改为 @Value 注入"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASE_CRYPTO_DIR = PROJECT_ROOT / "micrioservice-system" / "base-framework" / "base-crypto"

IMPORT_REPLACEMENTS = {
    "com.corp.config.ConfigClient": "org.springframework.beans.factory.annotation.Value",
    "com.corp.config.ConfigChangeListener": "org.springframework.beans.factory.annotation.Value",
}

CODE_REPLACEMENTS = [
    # configClient.getConfig("xxx") → @Value("${xxx}") 注入
    (re.compile(r'configClient\.getConfig\("(\w+)"\)'), r'/* TODO: 改为 @Value("${\1}") 注入 */ null'),
    (re.compile(r'configClient\.getConfig\("(\w+)",\s*(\w+)\)'), r'/* TODO: @Value("${\1:\2}") */ \2'),
    # 移除 ConfigClient 变量声明
    (re.compile(r'private\s+ConfigClient\s+\w+\s*;'), '/* ConfigClient 已移除，改用 @Value */'),
]


def update_java(file_path: Path):
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
        print(f"  已更新: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("更新 base-crypto")
    print("=" * 70)
    if not BASE_CRYPTO_DIR.exists():
        print("base-crypto 目录不存在")
        return
    total = sum(1 for j in BASE_CRYPTO_DIR.rglob("*.java") if update_java(j))
    print(f"\n共修改 {total} 个 Java 文件")


if __name__ == "__main__":
    main()
