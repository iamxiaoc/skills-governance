#!/usr/bin/env python3
"""扫描 base-framework 中所有引用二方件的封装类"""

from pathlib import Path
import re
import json

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASE_FRAMEWORK_DIR = PROJECT_ROOT / "micrioservice-system" / "base-framework"

CORP_PACKAGES = ["com.corp.trace", "com.corp.id", "com.corp.config", "com.corp.monitor"]


def scan_module(module_dir: Path):
    """扫描一个 base-framework 子 module 中的二方件引用"""
    refs = []
    for java in module_dir.rglob("*.java"):
        try:
            content = java.read_text(encoding="utf-8")
        except Exception:
            continue
        for pkg in CORP_PACKAGES:
            if pkg in content:
                # 找到 import 行
                for match in re.finditer(rf"import\s+({pkg}\.[\w.]+);", content):
                    refs.append({
                        "file": str(java.relative_to(PROJECT_ROOT)),
                        "import": match.group(1),
                        "package": pkg,
                    })
    return refs


def main():
    print("=" * 70)
    print("扫描 base-framework 中二方件引用")
    print("=" * 70)

    all_refs = []
    for module in BASE_FRAMEWORK_DIR.iterdir():
        if not module.is_dir():
            continue
        print(f"\n[{module.name}]")
        refs = scan_module(module)
        if refs:
            for r in refs:
                print(f"  {r['import']}")
                print(f"    文件: {r['file']}")
        else:
            print("  无二方件引用")
        all_refs.extend(refs)

    print(f"\n共发现 {len(all_refs)} 处引用")
    output = Path(__file__).parent / "framework_refs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_refs, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
