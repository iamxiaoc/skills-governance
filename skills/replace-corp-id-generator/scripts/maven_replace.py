#!/usr/bin/env python3
"""
修改 pom.xml：
1. base-dependency 中移除 corp-id-generator，添加部门自研 leaf
2. 所有微服务 pom 移除 corp-id-generator 依赖声明
"""

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

CORP_ID_GROUP = "com.corp.id"
CORP_ID_ARTIFACT = "corp-id-generator"
LEAF_GROUP = "com.dept.leaf"
LEAF_ARTIFACT = "leaf-id-generator"
LEAF_VERSION = "1.1.0"


def remove_corp_id_from_pom(pom_path: Path):
    """从 pom.xml 中移除 corp-id-generator 依赖"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return False

    modified = False
    for container in root.findall(".//m:dependencies", NS):
        for dep in list(container.findall("m:dependency", NS)):
            g = dep.find("m:groupId", NS)
            a = dep.find("m:artifactId", NS)
            if (g is not None and g.text and g.text.strip() == CORP_ID_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_ID_ARTIFACT):
                container.remove(dep)
                modified = True
                print(f"  移除依赖: {pom_path.relative_to(PROJECT_ROOT)}")
                break

    if modified:
        tree.write(pom_path, encoding="UTF-8", xml_declaration=True)
    return modified


def update_base_dependency():
    """在 base-dependency 中添加 leaf 依赖管理，移除 corp-id-generator"""
    base_pom = MICROSERVICE_DIR / "base-dependency" / "pom.xml"
    tree = ET.parse(base_pom)
    root = tree.getroot()

    # 添加 leaf.version property
    props = root.find("m:properties", NS)
    if props is not None:
        if props.find("m:leaf.version", NS) is None:
            elem = ET.SubElement(props, "leaf.version")
            elem.text = LEAF_VERSION
            print(f"  添加 property: leaf.version = {LEAF_VERSION}")

        # 移除 corp-id-generator.version
        corp_ver = props.find("m:corp-id-generator.version", NS)
        if corp_ver is not None:
            props.remove(corp_ver)
            print(f"  移除 property: corp-id-generator.version")

    # 在 dependencyManagement 中添加 leaf，移除 corp-id-generator
    dep_mgmt = root.find("m:dependencyManagement/m:dependencies", NS)
    if dep_mgmt is not None:
        # 移除 corp-id-generator
        for dep in list(dep_mgmt.findall("m:dependency", NS)):
            g = dep.find("m:groupId", NS)
            a = dep.find("m:artifactId", NS)
            if (g is not None and g.text and g.text.strip() == CORP_ID_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_ID_ARTIFACT):
                dep_mgmt.remove(dep)
                print(f"  移除 dependencyManagement: corp-id-generator")

        # 添加 leaf
        exists = any(
            d.find("m:groupId", NS) is not None and
            d.find("m:groupId", NS).text and
            d.find("m:groupId", NS).text.strip() == LEAF_GROUP
            for d in dep_mgmt.findall("m:dependency", NS)
        )
        if not exists:
            dep = ET.SubElement(dep_mgmt, "dependency")
            g = ET.SubElement(dep, "groupId")
            g.text = LEAF_GROUP
            a = ET.SubElement(dep, "artifactId")
            a.text = LEAF_ARTIFACT
            v = ET.SubElement(dep, "version")
            v.text = "${leaf.version}"
            print(f"  添加 dependencyManagement: {LEAF_GROUP}:{LEAF_ARTIFACT}")

    tree.write(base_pom, encoding="UTF-8", xml_declaration=True)
    print(f"  更新: {base_pom.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Maven 替换: corp-id-generator → Leaf")
    print("=" * 70)

    print("\n[Step 1] 更新 base-dependency...")
    update_base_dependency()

    print("\n[Step 2] 扫描所有 pom.xml 并移除 corp-id-generator...")
    pom_files = list(MICROSERVICE_DIR.rglob("pom.xml"))
    total = sum(1 for pom in pom_files if remove_corp_id_from_pom(pom))
    print(f"\n共修改 {total} 个 pom.xml")


if __name__ == "__main__":
    main()
