#!/usr/bin/env python3
"""验证移除版本后，所有依赖仍能从 base-dependency 解析到版本"""

from pathlib import Path
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def get_base_managed():
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


def verify_pom(pom_path: Path, managed: set):
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return []

    unmanaged = []
    for dep in root.findall(".//m:dependencies/m:dependency", NS):
        g = dep.find("m:groupId", NS)
        a = dep.find("m:artifactId", NS)
        v = dep.find("m:version", NS)
        if g is not None and a is not None and g.text and a.text:
            key = (g.text.strip(), a.text.strip())
            if v is None and key not in managed:
                unmanaged.append({
                    "coordinate": f"{key[0]}:{key[1]}",
                    "pomFile": str(pom_path.relative_to(PROJECT_ROOT)),
                })
    return unmanaged


def main():
    print("=" * 70)
    print("验证依赖版本解析")
    print("=" * 70)
    managed = get_base_managed()
    all_unmanaged = []
    for pom in MICROSERVICE_DIR.rglob("pom.xml"):
        all_unmanaged.extend(verify_pom(pom, managed))

    if all_unmanaged:
        print(f"\n⚠️  发现 {len(all_unmanaged)} 个未管理依赖:")
        for u in all_unmanaged:
            print(f"  {u['coordinate']}  @  {u['pomFile']}")
    else:
        print("\n✅ 所有依赖均能从 base-dependency 解析版本")


if __name__ == "__main__":
    main()
