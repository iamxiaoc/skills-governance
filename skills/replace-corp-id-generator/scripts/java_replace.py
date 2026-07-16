#!/usr/bin/env python3
"""
替换 Java 代码中 corp-id-generator 的 API 调用为 Leaf 等价实现。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

IMPORT_REPLACEMENTS = {
    "com.corp.id.IdGenerator": "com.dept.leaf.LeafIDGen",
    "com.corp.id.IdGeneratorFactory": "com.dept.leaf.LeafIDGenFactory",
}

CODE_REPLACEMENTS = [
    # 类名替换
    (re.compile(r"\bIdGeneratorFactory\b"), "LeafIDGenFactory"),
    (re.compile(r"\bIdGenerator\b"), "LeafIDGen"),
    # 工厂方法
    (re.compile(r"LeafIDGenFactory\.getDefault\(\)"), "LeafIDGenFactory.getDefault()"),
    # nextBizId 保持不变（Leaf 接口兼容）
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
    print("Java 替换: corp-id-generator → Leaf")
    print("=" * 70)

    java_files = list(MICROSERVICE_DIR.rglob("*.java"))
    total = sum(1 for j in java_files if replace_in_java(j))
    print(f"\n共修改 {total} 个 Java 文件")
    print("\n⚠️  需检查 Leaf 的 workerId 分配方式（依赖数据库）")


if __name__ == "__main__":
    main()
