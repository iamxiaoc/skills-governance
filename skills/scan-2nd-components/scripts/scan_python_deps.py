#!/usr/bin/env python3
"""
扫描 CI 流水线（Python 代码）中的二方件引用。
输出：corp_ci_common / corp_ci_registry 的引用情况。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CI_DIR = PROJECT_ROOT / "micrioservice-system" / "ci"

# Python 二方件模块前缀
CORP_PY_MODULES = ["corp_ci_common", "corp_ci_registry"]


def scan_python_imports(file_path: Path):
    """扫描 Python 文件中的 import 语句，找出二方件引用"""
    refs = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return refs

    for line in content.splitlines():
        stripped = line.strip()
        for mod in CORP_PY_MODULES:
            # 匹配 import corp_ci_xxx 或 from corp_ci_xxx import
            if re.match(rf"(import\s+{mod}(\s|$|\,))|(from\s+{mod}(\.|\s))", stripped):
                refs.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "line": stripped,
                    "module": mod,
                })
    return refs


def main():
    print("=" * 70)
    print("CI 流水线二方件引用扫描")
    print("=" * 70)

    if not CI_DIR.exists():
        print(f"CI 目录不存在: {CI_DIR}")
        return

    py_files = list(CI_DIR.rglob("*.py"))
    print(f"\n扫描到 {len(py_files)} 个 Python 文件\n")

    all_refs = []
    for py in py_files:
        refs = scan_python_imports(py)
        all_refs.extend(refs)

    if not all_refs:
        print("未发现二方件引用")
        return

    # 按模块分组
    grouped = {}
    for ref in all_refs:
        mod = ref["module"]
        if mod not in grouped:
            grouped[mod] = []
        grouped[mod].append(ref)

    print(f"共发现 {len(all_refs)} 处二方件引用，涉及 {len(grouped)} 个二方件\n")
    print("-" * 70)

    for mod, refs in grouped.items():
        print(f"\n二方件: {mod}")
        print(f"  引用数: {len(refs)}")
        seen_files = set()
        for ref in refs:
            if ref["file"] not in seen_files:
                print(f"  文件: {ref['file']}")
                seen_files.add(ref["file"])
        print(f"  引用语句示例:")
        for ref in refs[:3]:
            print(f"    - {ref['line']}")
        if len(refs) > 3:
            print(f"    ... 及其余 {len(refs) - 3} 处")

    print("\n" + "=" * 70)
    print("⚠️  Python 二方件需替换为开源方案或部门自研组件")
    print("=" * 70)


if __name__ == "__main__":
    main()
