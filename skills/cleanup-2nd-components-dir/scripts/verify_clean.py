#!/usr/bin/env python3
"""验证删除二方件后项目结构完整"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

EXPECTED_DIRS = [
    "base-dependency",
    "base-framework",
    "user-module",
    "order-module",
    "product-module",
    "ci",
    "2nd-components",
]


def main():
    print("=" * 70)
    print("验证项目结构完整性")
    print("=" * 70)

    all_ok = True
    for d in EXPECTED_DIRS:
        path = MICROSERVICE_DIR / d
        if path.exists():
            print(f"  ✅ {d}/")
        else:
            print(f"  ❌ {d}/ (缺失)")
            all_ok = False

    # 检查 2nd-components 下剩余的二方件
    comp_dir = MICROSERVICE_DIR / "2nd-components"
    if comp_dir.exists():
        remaining = [d.name for d in comp_dir.iterdir() if d.is_dir()]
        print(f"\n2nd-components 下剩余: {', '.join(remaining) if remaining else '(空)'}")

    if all_ok:
        print("\n✅ 项目结构完整")
    else:
        print("\n❌ 项目结构不完整，需检查")


if __name__ == "__main__":
    main()
