#!/usr/bin/env python3
"""
对比改造前后同一接口的响应体。
用法：python diff_response.py --before before.json --after after.json [--ignore-fields field1,field2]
"""

import argparse
import json
from pathlib import Path


# 默认需剔除的动态字段（忽略其值）
DEFAULT_IGNORE_FIELDS = {
    "timestamp", "ts", "time", "currentTime",
    "traceId", "spanId", "requestId", "trace",
    "id", "userId", "orderId", "productId",
    "createdAt", "updatedAt", "createTime", "updateTime",
    "token", "accessToken", "refreshToken",
    "signature", "sign",
}


def flatten_json(obj, prefix=""):
    """将嵌套 JSON 展平为 {path: value} 形式"""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            items.update(flatten_json(v, key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            key = f"{prefix}[{i}]"
            items.update(flatten_json(item, key))
    else:
        items[prefix] = obj
    return items


def compare_structure(before_flat, after_flat):
    """对比结构差异"""
    before_keys = set(before_flat.keys())
    after_keys = set(after_flat.keys())

    missing = before_keys - after_keys
    added = after_keys - before_keys
    common = before_keys & after_keys

    return missing, added, common


def compare_values(before_flat, after_flat, common_keys, ignore_fields):
    """对比值差异（忽略动态字段）"""
    diffs = []
    for key in common_keys:
        # 检查是否是需要忽略的字段
        last_segment = key.split(".")[-1].split("[")[0]
        if last_segment in ignore_fields:
            continue

        before_val = before_flat[key]
        after_val = after_flat[key]

        if before_val != after_val:
            diffs.append({
                "field": key,
                "before": before_val,
                "after": after_val,
            })

        # 类型差异
        if type(before_val) != type(after_val):
            diffs.append({
                "field": key,
                "beforeType": type(before_val).__name__,
                "afterType": type(after_val).__name__,
            })

    return diffs


def main():
    parser = argparse.ArgumentParser(description="对比接口响应体")
    parser.add_argument("--before", required=True, help="改造前响应 JSON 文件")
    parser.add_argument("--after", required=True, help="改造后响应 JSON 文件")
    parser.add_argument("--ignore-fields", default="", help="额外忽略的字段（逗号分隔）")
    parser.add_argument("--api", default="", help="接口路径（用于输出标识）")
    args = parser.parse_args()

    # 加载 JSON
    with open(args.before, "r", encoding="utf-8") as f:
        before = json.load(f)
    with open(args.after, "r", encoding="utf-8") as f:
        after = json.load(f)

    # 忽略字段集合
    ignore_fields = set(DEFAULT_IGNORE_FIELDS)
    if args.ignore_fields:
        ignore_fields.update(args.ignore_fields.split(","))

    api_name = args.api or "unknown"

    print(f"=== 接口对比: {api_name} ===\n")

    # 展平
    before_flat = flatten_json(before)
    after_flat = flatten_json(after)

    # 结构差异
    missing, added, common = compare_structure(before_flat, after_flat)

    print("[结构差异]")
    if missing:
        print("  ❌ 改造后缺失字段:")
        for f in sorted(missing):
            print(f"      - {f}")
    else:
        print("  ✅ 无缺失字段")

    if added:
        print("  ❌ 改造后新增字段:")
        for f in sorted(added):
            print(f"      - {f}")
    else:
        print("  ✅ 无新增字段")

    # 值差异
    diffs = compare_values(before_flat, after_flat, common, ignore_fields)

    print("\n[值差异]（已剔除动态字段）")
    if diffs:
        for d in diffs:
            if "beforeType" in d:
                print(f"  ⚠️  {d['field']}: {d['beforeType']} → {d['afterType']}")
            else:
                print(f"  ❌ {d['field']}: {d['before']} → {d['after']}")
    else:
        print("  ✅ 无值差异")

    # 结论
    has_diff = bool(missing or added or diffs)
    print(f"\n结论: {'❌ 存在差异，需人工确认' if has_diff else '✅ 接口响应一致'}")


if __name__ == "__main__":
    main()
