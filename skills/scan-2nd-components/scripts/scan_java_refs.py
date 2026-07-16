#!/usr/bin/env python3
"""
扫描所有 .java 文件中 com.corp.* 的 import 语句，
统计二方件的接口/方法在业务代码中的调用点。
"""

import re
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

# 二方件 Java 包前缀
CORP_JAVA_PACKAGES = [
    "com.corp.trace",
    "com.corp.id",
    "com.corp.config",
    "com.corp.monitor",
]


def scan_java_imports(file_path: Path):
    """扫描 Java 文件中的 import 语句"""
    refs = []
    try:
        content = file_text = file_path.read_text(encoding="utf-8")
    except Exception:
        return refs

    for match in re.finditer(r"^import\s+(com\.corp\.\w+(?:\.\w+)*)\s*;", content, re.MULTILINE):
        refs.append({
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "package": match.group(1),
        })
    return refs


def scan_java_method_calls(file_path: Path):
    """扫描 Java 文件中对二方件类/方法的调用点"""
    calls = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return calls

    # 查找 TraceUtils. / IdGeneratorFactory. / ConfigClient. / MonitorUtils. 等调用
    patterns = [
        (r"TraceUtils\.(\w+)\(", "TraceUtils"),
        (r"TraceContext\.(\w+)\(", "TraceContext"),
        (r"IdGeneratorFactory\.(\w+)\(", "IdGeneratorFactory"),
        (r"IdGenerator\b.*?\.(\w+)\(", "IdGenerator"),
        (r"ConfigClient\b.*?\.(\w+)\(", "ConfigClient"),
        (r"MonitorUtils\.(\w+)\(", "MonitorUtils"),
        (r"MonitorReporter\b.*?\.(\w+)\(", "MonitorReporter"),
    ]

    for pattern, class_name in patterns:
        for match in re.finditer(pattern, content):
            calls.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "className": class_name,
                "method": match.group(1),
            })
    return calls


def main():
    print("=" * 70)
    print("Java 代码中二方件引用与调用扫描")
    print("=" * 70)

    java_files = list(MICROSERVICE_DIR.rglob("*.java"))
    print(f"\n扫描到 {len(java_files)} 个 Java 文件\n")

    all_imports = []
    all_calls = []

    for java in java_files:
        all_imports.extend(scan_java_imports(java))
        all_calls.extend(scan_java_method_calls(java))

    # 按 package 分组 import
    imports_grouped = defaultdict(list)
    for imp in all_imports:
        imports_grouped[imp["package"]].append(imp["file"])

    print("【import 统计】")
    for pkg, files in sorted(imports_grouped.items()):
        print(f"\n  {pkg}")
        print(f"    引用文件数: {len(files)}")
        for f in files[:5]:
            print(f"      - {f}")
        if len(files) > 5:
            print(f"      ... 及其余 {len(files) - 5} 个文件")

    # 按 class 分组方法调用
    calls_grouped = defaultdict(lambda: defaultdict(set))
    for call in all_calls:
        calls_grouped[call["className"]][call["method"]].add(call["file"])

    print("\n" + "=" * 70)
    print("【方法调用统计】")
    for cls, methods in sorted(calls_grouped.items()):
        print(f"\n  {cls}")
        for method, files in sorted(methods.items()):
            print(f"    .{method}()  被 {len(files)} 个文件调用")
            for f in list(files)[:2]:
                print(f"        - {f}")

    # 保存 JSON 结果
    output = {
        "imports": {k: v for k, v in imports_grouped.items()},
        "calls": {
            cls: {method: list(files) for method, files in methods.items()}
            for cls, methods in calls_grouped.items()
        },
    }
    output_file = Path(__file__).parent / "java_refs_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存至: {output_file}")


if __name__ == "__main__":
    main()
