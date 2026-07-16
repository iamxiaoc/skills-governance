#!/usr/bin/env python3
"""修改 pom.xml：移除 corp-config-client，添加 spring-cloud-config-client"""

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

CORP_CFG_GROUP = "com.corp.config"
CORP_CFG_ARTIFACT = "corp-config-client"
SCC_GROUP = "org.springframework.cloud"
SCC_ARTIFACT = "spring-cloud-starter-config"
SCC_VERSION = "2022.0.4"


def remove_corp_config(pom_path: Path):
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
            if (g is not None and g.text and g.text.strip() == CORP_CFG_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_CFG_ARTIFACT):
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
        if props.find("m:spring-cloud.version", NS) is None:
            elem = ET.SubElement(props, "spring-cloud.version")
            elem.text = SCC_VERSION
            print(f"  添加 property: spring-cloud.version = {SCC_VERSION}")
        corp_ver = props.find("m:corp-config-client.version", NS)
        if corp_ver is not None:
            props.remove(corp_ver)
            print(f"  移除 property: corp-config-client.version")

    dep_mgmt = root.find("m:dependencyManagement/m:dependencies", NS)
    if dep_mgmt is not None:
        for dep in list(dep_mgmt.findall("m:dependency", NS)):
            g = dep.find("m:groupId", NS)
            a = dep.find("m:artifactId", NS)
            if (g is not None and g.text and g.text.strip() == CORP_CFG_GROUP and
                    a is not None and a.text and a.text.strip() == CORP_CFG_ARTIFACT):
                dep_mgmt.remove(dep)
                print(f"  移除 dependencyManagement: corp-config-client")

        exists = any(
            d.find("m:artifactId", NS) is not None and
            d.find("m:artifactId", NS).text and
            d.find("m:artifactId", NS).text.strip() == SCC_ARTIFACT
            for d in dep_mgmt.findall("m:dependency", NS)
        )
        if not exists:
            dep = ET.SubElement(dep_mgmt, "dependency")
            g = ET.SubElement(dep, "groupId"); g.text = SCC_GROUP
            a = ET.SubElement(dep, "artifactId"); a.text = SCC_ARTIFACT
            v = ET.SubElement(dep, "version"); v.text = "${spring-cloud.version}"
            print(f"  添加 dependencyManagement: {SCC_GROUP}:{SCC_ARTIFACT}")

    tree.write(base_pom, encoding="UTF-8", xml_declaration=True)
    print(f"  更新: {base_pom.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Maven 替换: corp-config-client → Spring Cloud Config")
    print("=" * 70)

    print("\n[Step 1] 更新 base-dependency...")
    update_base_dependency()

    print("\n[Step 2] 扫描所有 pom.xml...")
    pom_files = list(MICROSERVICE_DIR.rglob("pom.xml"))
    total = sum(1 for p in pom_files if remove_corp_config(p))
    print(f"\n共修改 {total} 个 pom.xml")


if __name__ == "__main__":
    main()
