#!/usr/bin/env python3
"""删除指定的二方件源码目录"""

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
COMPONENTS_DIR = PROJECT_ROOT / "micrioservice-system" / "2nd-components"

COMPONENTS = [
    "corp-trace",
    "corp-id-generator",
    "corp-config-client",
    "corp-monitor",
    "corp-ci-common",
    "corp-ci-registry",
]


def delete_component(component: str):
    target = COMPONENTS_DIR / component
    if not target.exists():
        print(f"目录不存在: {target}")
        return False

    shutil.rmtree(target)
    print(f"已删除: {target.relative_to(PROJECT_ROOT)}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", required=True, choices=COMPONENTS)
    args = parser.parse_args()

    print(f"⚠️  即将删除 {args.component} 源码目录")
    print("请确保已运行 check_safe_to_delete.py 确认无残留引用")

    delete_component(args.component)


if __name__ == "__main__":
    main()
