#!/usr/bin/env python3
"""
提取指定二方件在业务代码中的具体 API 使用情况。
支持参数：
  --component <名称>   指定单个二方件（corp-trace / corp-id-generator / corp-config-client / corp-monitor）
  --all                提取全部二方件
"""

import argparse
import re
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

# 二方件 → 类名映射
COMPONENT_CLASSES = {
    "corp-trace": {
        "package": "com.corp.trace",
        "classes": ["TraceUtils", "TraceContext"],
    },
    "corp-id-generator": {
        "package": "com.corp.id",
        "classes": ["IdGenerator", "IdGeneratorFactory"],
    },
    "corp-config-client": {
        "package": "com.corp.config",
        "classes": ["ConfigClient", "ConfigChangeListener"],
    },
    "corp-monitor": {
        "package": "com.corp.monitor",
        "classes": ["MonitorUtils", "MonitorReporter"],
    },
}


def extract_class_usage(java_file: Path, class_names):
    """提取 Java 文件中对指定类的使用"""
    usages = []
    try:
        content = java_file.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception:
        return usages

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # 跳过注释行
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        for cls in class_names:
            # 静态方法调用：ClassName.method()
            for match in re.finditer(rf"\b{cls}\.(\w+)\s*\(", stripped):
                usages.append({
                    "file": str(java_file.relative_to(PROJECT_ROOT)),
                    "line": i,
                    "class": cls,
                    "method": match.group(1),
                    "type": "static_call",
                    "context": stripped,
                })

            # 实例方法调用：需要先有变量声明，这里简化匹配 xxx.method()
            # 变量声明：ClassName xxx = ...
            if re.search(rf"\b{cls}\s+\w+\s*=", stripped):
                usages.append({
                    "file": str(java_file.relative_to(PROJECT_ROOT)),
                    "line": i,
                    "class": cls,
                    "method": "(instantiation)",
                    "type": "declaration",
                    "context": stripped,
                })

            # new ClassName(
            if re.search(rf"\bnew\s+{cls}\s*\(", stripped):
                usages.append({
                    "file": str(java_file.relative_to(PROJECT_ROOT)),
                    "line": i,
                    "class": cls,
                    "method": "(constructor)",
                    "type": "instantiation",
                    "context": stripped,
                })

            # implements ClassName（接口实现）
            if re.search(rf"\bimplements\s+.*\b{cls}\b", stripped):
                usages.append({
                    "file": str(java_file.relative_to(PROJECT_ROOT)),
                    "line": i,
                    "class": cls,
                    "method": "(implements)",
                    "type": "implements",
                    "context": stripped,
                })

    return usages


def extract_component(component_name: str):
    """提取单个二方件的使用情况"""
    if component_name not in COMPONENT_CLASSES:
        print(f"未知二方件: {component_name}")
        print(f"支持: {', '.join(COMPONENT_CLASSES.keys())}")
        return

    info = COMPONENT_CLASSES[component_name]
    pkg = info["package"]
    classes = info["classes"]

    print(f"\n{'=' * 70}")
    print(f"=== {component_name} 用法提取 ===")
    print(f"{'=' * 70}")
    print(f"包: {pkg}")
    print(f"类: {', '.join(classes)}")

    java_files = list(MICROSERVICE_DIR.rglob("*.java"))

    all_usages = []
    for java in java_files:
        usages = extract_class_usage(java, classes)
        all_usages.extend(usages)

    if not all_usages:
        print("\n未发现任何调用")
        return

    # 按类分组
    by_class = defaultdict(list)
    for u in all_usages:
        by_class[u["class"]].append(u)

    for cls in classes:
        usages = by_class.get(cls, [])
        print(f"\n[类] {cls}")
        if not usages:
            print(f"  无调用记录")
            continue

        # 按方法分组
        by_method = defaultdict(list)
        for u in usages:
            by_method[u["method"]].append(u)

        for method, calls in sorted(by_method.items()):
            print(f"  方法 {method}    调用 {len(calls)} 次")
            for c in calls[:3]:
                print(f"    - {c['file']}:{c['line']}")
                print(f"        {c['context']}")
            if len(calls) > 3:
                print(f"    ... 及其余 {len(calls) - 3} 次")

    # 保存 JSON
    output_file = Path(__file__).parent / f"{component_name}_usage.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_usages, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存至: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="提取二方件 API 使用情况")
    parser.add_argument(
        "--component",
        choices=list(COMPONENT_CLASSES.keys()),
        help="指定要提取的二方件",
    )
    parser.add_argument("--all", action="store_true", help="提取全部二方件")
    args = parser.parse_args()

    if args.all:
        for name in COMPONENT_CLASSES:
            extract_component(name)
    elif args.component:
        extract_component(args.component)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
