#!/usr/bin/env python3
"""扫描 CI 目录下所有 Python 二方件 import"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CI_DIR = PROJECT_ROOT / "micrioservice-system" / "ci"

CORP_MODULES = ["corp_ci_common", "corp_ci_registry"]


def scan_imports(py_file: Path):
    refs = []
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        return refs
    for line in content.splitlines():
        for mod in CORP_MODULES:
            if re.match(rf"(import\s+{mod}(\s|$|,))|(from\s+{mod}(\.|\s))", line.strip()):
                refs.append({
                    "file": str(py_file.relative_to(PROJECT_ROOT)),
                    "line": line.strip(),
                    "module": mod,
                })
    return refs


def main():
    print("=" * 70)
    print("扫描 CI Python 二方件 import")
    print("=" * 70)
    all_refs = []
    for py in CI_DIR.rglob("*.py"):
        refs = scan_imports(py)
        all_refs.extend(refs)

    grouped = {}
    for r in all_refs:
        grouped.setdefault(r["module"], []).append(r)

    for mod, refs in grouped.items():
        print(f"\n[{mod}] 引用 {len(refs)} 处")
        for r in refs:
            print(f"  {r['file']}")
            print(f"    {r['line']}")

    print(f"\n共发现 {len(all_refs)} 处引用")


if __name__ == "__main__":
    main()
