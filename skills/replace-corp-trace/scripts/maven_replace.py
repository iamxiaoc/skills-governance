#!/usr/bin/env python3
"""
修改 pom.xml：
1. 在 base-dependency 中移除 corp-trace，添加 opentelemetry-bom
2. 在所有微服务 pom 中移除 corp-trace 依赖声明
3. 确保 opentelemetry 版本统一由 base-dependency 管理
"""

import re
from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
# 注册命名空间，避免输出时带 ns0 前缀
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

CORP_TRACE_GROUP = "com.corp.trace"
CORP_TRACE_ARTIFACT = "corp-trace"

OTEL_BOM_GROUP = "io.opentelemetry"
OTEL_BOM_ARTIFACT = "opentelemetry-bom"
OTEL_VERSION = "1.32.0"


def remove_corp_trace_from_pom(pom_path: Path):
    """从 pom.xml 中移除 corp-trace 依赖声明"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return False

    modified = False

    # 在 dependencies 和 dependencyManagement 中查找 corp-trace
    for dep in root.findall(".//m:dependency", NS):
        group_elem = dep.find("m:groupId", NS)
        artifact_elem = dep.find("m:artifactId", NS)

        if group_elem is None or artifact_elem is None:
            continue

        if (group_elem.text and group_elem.text.strip() == CORP_TRACE_GROUP and
                artifact_elem.text and artifact_elem.text.strip() == CORP_TRACE_ARTIFACT):

            parent = dep.getparent() if hasattr(dep, "getparent") else None
            # 标准 ElementTree 没有 getparent，需要找到父节点
            for container in root.findall(".//m:dependencies", NS):
                if dep in list(container):
                    container.remove(dep)
                    modified = True
                    break
            for container in root.findall(".//m:dependencyManagement/m:dependencies", NS):
                if dep in list(container):
                    container.remove(dep)
                    modified = True
                    break

    if modified:
        tree.write(pom_path, encoding="UTF-8", xml_declaration=True)
        print(f"  已移除 corp-trace: {pom_path.relative_to(PROJECT_ROOT)}")

    return modified


def add_otel_to_base_dependency():
    """在 base-dependency 根 pom 中添加 OpenTelemetry BOM"""
    base_dep_pom = MICROSERVICE_DIR / "base-dependency" / "pom.xml"

    tree = ET.parse(base_dep_pom)
    root = tree.getroot()

    # 1. 在 properties 中添加 opentelemetry.version
    props = root.find("m:properties", NS)
    if props is not None:
        existing = props.find("m:opentelemetry.version", NS)
        if existing is None:
            new_prop = ET.SubElement(props, "opentelemetry.version")
            new_prop.text = OTEL_VERSION
            print(f"  添加 property: opentelemetry.version = {OTEL_VERSION}")

    # 2. 在 dependencyManagement 中添加 opentelemetry-bom
    dep_mgmt_deps = root.find("m:dependencyManagement/m:dependencies", NS)
    if dep_mgmt_deps is not None:
        # 检查是否已存在
        exists = False
        for dep in dep_mgmt_deps.findall("m:dependency", NS):
            g = dep.find("m:groupId", NS)
            if g is not None and g.text and g.text.strip() == OTEL_BOM_GROUP:
                exists = True
                break

        if not exists:
            new_dep = ET.SubElement(dep_mgmt_deps, "dependency")
            g = ET.SubElement(new_dep, "groupId")
            g.text = OTEL_BOM_GROUP
            a = ET.SubElement(new_dep, "artifactId")
            a.text = OTEL_BOM_ARTIFACT
            v = ET.SubElement(new_dep, "version")
            v.text = "${opentelemetry.version}"
            t = ET.SubElement(new_dep, "type")
            t.text = "pom"
            s = ET.SubElement(new_dep, "scope")
            s.text = "import"
            print(f"  添加 BOM: {OTEL_BOM_GROUP}:{OTEL_BOM_ARTIFACT}")

    # 3. 同时移除 corp-trace 的 dependencyManagement 声明
    if dep_mgmt_deps is not None:
        for dep in list(dep_mgmt_deps.findall("m:dependency", NS)):
            g = dep.find("m:groupId", NS)
            a = dep.find("m:artifactId", NS)
            if (g is not None and g.text and g.text.strip() == CORP_TRACE_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_TRACE_ARTIFACT):
                dep_mgmt_deps.remove(dep)
                print(f"  移除 dependencyManagement 中的 corp-trace 声明")

    # 4. 移除 properties 中的 corp-trace.version
    if props is not None:
        corp_trace_ver = props.find("m:corp-trace.version", NS)
        if corp_trace_ver is not None:
            props.remove(corp_trace_ver)
            print(f"  移除 property: corp-trace.version")

    tree.write(base_dep_pom, encoding="UTF-8", xml_declaration=True)
    print(f"  更新: {base_dep_pom.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Maven pom.xml 依赖替换: corp-trace → OpenTelemetry")
    print("=" * 70)

    # Step 1: 更新 base-dependency
    print("\n[Step 1] 更新 base-dependency...")
    add_otel_to_base_dependency()

    # Step 2: 扫描所有 pom.xml，移除 corp-trace 依赖
    print("\n[Step 2] 扫描所有 pom.xml 并移除 corp-trace...")
    pom_files = list(MICROSERVICE_DIR.rglob("pom.xml"))
    total_modified = 0
    for pom in pom_files:
        if remove_corp_trace_from_pom(pom):
            total_modified += 1

    print(f"\n共修改 {total_modified} 个 pom.xml 文件")
    print("\n⚠️  后续需手动检查：")
    print("  1. 各微服务是否需要显式声明 opentelemetry-api 依赖")
    print("  2. Dockerfile 是否需要添加 otel-agent")


if __name__ == "__main__":
    main()
