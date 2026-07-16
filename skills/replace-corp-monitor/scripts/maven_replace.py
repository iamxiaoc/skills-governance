#!/usr/bin/env python3
"""修改 pom.xml：移除 corp-monitor，添加 micrometer-registry-prometheus"""

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

CORP_MON_GROUP = "com.corp.monitor"
CORP_MON_ARTIFACT = "corp-monitor"
MM_GROUP = "io.micrometer"
MM_ARTIFACT = "micrometer-registry-prometheus"


def remove_corp_monitor(pom_path: Path):
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
            if (g is not None and g.text and g.text.strip() == CORP_MON_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_MON_ARTIFACT):
                container.remove(dep)
                modified = True
                print(f"  移除依赖: {pom_path.relative_to(PROJECT_ROOT)}")
                break
    if modified:
        tree.write(pom_path, encoding="UTF-8", xml_declaration=True)
    return modified


def update_base_dependency():
    base_pom = MICROSERVICE_DIR / "base-dependency" / "pom.xml"
    tree = ET.parse(base_pom)
    root = tree.getroot()

    props = root.find("m:properties", NS)
    if props is not None:
        corp_ver = props.find("m:corp-monitor.version", NS)
        if corp_ver is not None:
            props.remove(corp_ver)
            print(f"  移除 property: corp-monitor.version")

    dep_mgmt = root.find("m:dependencyManagement/m:dependencies", NS)
    if dep_mgmt is not None:
        for dep in list(dep_mgmt.findall("m:dependency", NS)):
            g = dep.find("m:groupId", NS)
            a = dep.find("m:artifactId", NS)
            if (g is not None and g.text and g.text.strip() == CORP_MON_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_MON_ARTIFACT):
                dep_mgmt.remove(dep)
                print(f"  移除 dependencyManagement: corp-monitor")

        exists = any(
            d.find("m:artifactId", NS) is not None and
            d.find("m:artifactId", NS).text and
            d.find("m:artifactId", NS).text.strip() == MM_ARTIFACT
            for d in dep_mgmt.findall("m:dependency", NS)
        )
        if not exists:
            dep = ET.SubElement(dep_mgmt, "dependency")
            g = ET.SubElement(dep, "groupId"); g.text = MM_GROUP
            a = ET.SubElement(dep, "artifactId"); a.text = MM_ARTIFACT
            print(f"  添加 dependencyManagement: {MM_GROUP}:{MM_ARTIFACT}（版本由 spring-boot BOM 管理）")

    tree.write(base_pom, encoding="UTF-8", xml_declaration=True)


def main():
    print("=" * 70)
    print("Maven 替换: corp-monitor → Micrometer + Prometheus")
    print("=" * 70)
    print("\n[Step 1] 更新 base-dependency...")
    update_base_dependency()
    print("\n[Step 2] 扫描所有 pom.xml...")
    pom_files = list(MICROSERVICE_DIR.rglob("pom.xml"))
    total = sum(1 for p in pom_files if remove_corp_monitor(p))
    print(f"\n共修改 {total} 个 pom.xml")


if __name__ == "__main__":
    main()
