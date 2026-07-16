#!/usr/bin/env python3
"""
扫描所有 pom.xml 中二方件（com.corp.*）的依赖声明。
输出：二方件坐标、版本、版本管理位置、引用模块清单。
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# 项目根目录（脚本位于 skills/scan-2nd-components/scripts/ 下）
PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

# 需要扫描的二方件 groupId 前缀
CORP_GROUP_PREFIXES = [
    "com.corp.trace",
    "com.corp.id",
    "com.corp.config",
    "com.corp.monitor",
]

# Maven POM 命名空间
NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def find_all_pom_files(base_dir: Path):
    """递归查找所有 pom.xml 文件"""
    return list(base_dir.rglob("pom.xml"))


def parse_pom_dependencies(pom_path: Path):
    """解析 pom.xml 中的依赖声明，返回二方件依赖列表"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return []

    deps = []
    # 查找 dependencies 下的 dependency 节点（包括 dependencyManagement）
    for dep in root.findall(".//m:dependency", NS):
        group_id_elem = dep.find("m:groupId", NS)
        artifact_id_elem = dep.find("m:artifactId", NS)
        version_elem = dep.find("m:version", NS)

        if group_id_elem is None or artifact_id_elem is None:
            continue

        group_id = group_id_elem.text.strip() if group_id_elem.text else ""
        artifact_id = artifact_id_elem.text.strip() if artifact_id_elem.text else ""

        # 仅关注 com.corp.* 的二方件
        if not any(group_id.startswith(prefix) for prefix in CORP_GROUP_PREFIXES):
            continue

        version = ""
        if version_elem is not None and version_elem.text:
            version = version_elem.text.strip()

        deps.append({
            "groupId": group_id,
            "artifactId": artifact_id,
            "version": version,
            "versionDefined": version != "",  # 是否在此 pom 中直接定义了版本
            "pomFile": str(pom_path.relative_to(PROJECT_ROOT)),
        })

    return deps


def parse_pom_properties(pom_path: Path):
    """解析 pom.xml 中的 properties，提取二方件版本变量"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return {}

    props = {}
    props_elem = root.find("m:properties", NS)
    if props_elem is not None:
        for child in props_elem:
            # 去除命名空间前缀
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child.text:
                props[tag] = child.text.strip()

    return props


def main():
    print("=" * 70)
    print("二方件 Maven 依赖扫描")
    print("=" * 70)

    pom_files = find_all_pom_files(MICROSERVICE_DIR)
    print(f"\n扫描到 {len(pom_files)} 个 pom.xml 文件\n")

    # 收集所有二方件依赖
    all_deps = []
    for pom in pom_files:
        deps = parse_pom_dependencies(pom)
        all_deps.extend(deps)

    # 收集 base-dependency 中定义的版本变量
    base_dep_pom = MICROSERVICE_DIR / "base-dependency" / "pom.xml"
    base_properties = parse_pom_properties(base_dep_pom) if base_dep_pom.exists() else {}

    # 按二方件分组
    grouped = {}
    for dep in all_deps:
        key = f"{dep['groupId']}:{dep['artifactId']}"
        if key not in grouped:
            grouped[key] = {
                "groupId": dep["groupId"],
                "artifactId": dep["artifactId"],
                "version": dep["version"],
                "references": [],
            }
        grouped[key]["references"].append({
            "pomFile": dep["pomFile"],
            "versionDefined": dep["versionDefined"],
        })

    # 输出结果
    print(f"共发现 {len(grouped)} 个二方件依赖\n")
    print("-" * 70)

    for key, info in grouped.items():
        print(f"\n二方件: {key}")
        print(f"  版本: {info['version'] or '(未在此处声明，依赖 base-dependency 管理)'}")
        print(f"  引用数: {len(info['references'])}")

        # 检查版本是否在微服务 pom 中被直接写死
        hardcoded = [r for r in info["references"] if r["versionDefined"]]
        if hardcoded:
            print(f"  ⚠️  以下 pom 中直接写死了版本号:")
            for ref in hardcoded:
                print(f"      - {ref['pomFile']}")

        print(f"  引用位置:")
        for ref in info["references"]:
            version_note = f" (版本: {ref['versionDefined']})" if ref["versionDefined"] else ""
            print(f"      - {ref['pomFile']}{version_note}")

    # 输出 JSON 格式供后续脚本使用
    output_file = Path(__file__).parent / "maven_deps_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存至: {output_file}")


if __name__ == "__main__":
    main()
