#!/usr/bin/env python3
"""
运行方法对比：读取 before/after 两份输出文件，对比是否一致。
用法：python run_comparison.py --method IdGenService.nextId --before before.json --after after.json
"""

import argparse
import json
from pathlib import Path


def compare(before, after):
    """对比两组输出"""
    if len(before) != len(after):
        return [f"用例数不一致: before={len(before)}, after={len(after)}"]

    diffs = []
    for i, (b, a) in enumerate(zip(before, after)):
        for key in set(list(b.keys()) + list(a.keys())):
            b_val = b.get(key, "<missing>")
            a_val = a.get(key, "<missing>")
            if b_val != a_val:
                diffs.append(f"用例 {i+1} 字段 '{key}': before={b_val}, after={a_val}")
    return diffs


def main():
    parser = argparse.ArgumentParser(description="对比方法输出")
    parser.add_argument("--method", required=True, help="方法名")
    parser.add_argument("--before", required=True, help="改造前输出 JSON")
    parser.add_argument("--after", required=True, help="改造后输出 JSON")
    args = parser.parse_args()

    with open(args.before, "r", encoding="utf-8") as f:
        before = json.load(f)
    with open(args.after, "r", encoding="utf-8") as f:
        after = json.load(f)

    print(f"=== 方法对比: {args.method} ===\n")

    diffs = compare(before, after)
    if diffs:
        print("❌ 存在差异:")
        for d in diffs:
            print(f"  - {d}")
    else:
        print("✅ 方法行为一致")


if __name__ == "__main__":
    main()
