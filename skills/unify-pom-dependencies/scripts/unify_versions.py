#!/usr/bin/env python3
"""移除微服务 pom.xml 中写死的版本标签（仅移除 base-dependency 已管理的依赖）"""

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

SERVICE_MODULES = ["user-module", "order-module", "product-module"]


def get_base_managed_coordinates():
    """获取 base-dependency 中已管理的依赖坐标集合"""
    base_pom = MICROSERVICE_DIR / "base-dependency" / "pom.xml"
    tree = ET.parse(base_pom)
    root = tree.getroot()

    managed = set()
    for dep in root.findall(".//m:dependencyManagement/m:dependencies/m:dependency", NS):
        g = dep.find("m:groupId", NS)
        a = dep.find("m:artifactId", NS)
        if g is not None and a is not None and g.text and a.text:
            managed.add((g.text.strip(), a.text.strip()))
    return managed


def remove_versions(pom_path: Path, managed: set):
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return 0

    removed = 0
    for dep in root.findall(".//m:dependencies/m:dependency", NS):
        g = dep.find("m:groupId", NS)
        a = dep.find("m:artifactId", NS)
        v = dep.find("m:version", NS)
        if g is not None and a is not None and v is not None:
            key = (g.text.strip(), a.text.strip()) if g.text and a.text else None
            if key and key in managed:
                dep.remove(v)
                removed += 1
                print(f"  移除版本: {key[0]}:{key[1]} @ {pom_path.relative_to(PROJECT_ROOT)}")

    if removed > 0:
        tree.write(pom_path, encoding="UTF-8", xml_declaration=True)
    return removed


def main():
    print("=" * 70)
    print("移除微服务 pom.xml 中写死的版本标签")
    print("=" * 70)

    managed = get_base_managed_coordinates()
    print(f"\nbase-dependency 管理 {len(managed)} 个依赖坐标\n")

    total = 0
    for mod in SERVICE_MODULES:
        mod_dir = MICROSERVICE_DIR / mod
        if not mod_dir.exists():
            continue
        print(f"[{mod}]")
        for pom in mod_dir.rglob("pom.xml"):
            total += remove_versions(pom, managed)

    print(f"\n共移除 {total} 处版本标签")


if __name__ == "__main__":
    main()
