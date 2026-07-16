#!/usr/bin/env python3
"""扫描所有微服务 pom.xml 中写死版本的依赖"""

from pathlib import Path
import xml.etree.ElementTree as ET
import json

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"
NS = {"m": "http://maven.apache.org/POM/4.0.0"}

# 微服务模块目录
SERVICE_MODULES = ["user-module", "order-module", "product-module"]


def scan_pom(pom_path: Path):
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
    except ET.ParseError:
        return []

    hardcoded = []
    for dep in root.findall(".//m:dependencies/m:dependency", NS):
        g = dep.find("m:groupId", NS)
        a = dep.find("m:artifactId", NS)
        v = dep.find("m:version", NS)
        if g is not None and a is not None and v is not None:
            if g.text and a.text and v.text:
                hardcoded.append({
                    "groupId": g.text.strip(),
                    "artifactId": a.text.strip(),
                    "version": v.text.strip(),
                    "pomFile": str(pom_path.relative_to(PROJECT_ROOT)),
                })
    return hardcoded


def main():
    print("=" * 70)
    print("扫描微服务 pom.xml 中写死版本的依赖")
    print("=" * 70)

    all_hardcoded = []
    for mod in SERVICE_MODULES:
        mod_dir = MICROSERVICE_DIR / mod
        if not mod_dir.exists():
            continue
        print(f"\n[{mod}]")
        for pom in mod_dir.rglob("pom.xml"):
            found = scan_pom(pom)
            if found:
                for h in found:
                    print(f"  {h['groupId']}:{h['artifactId']} = {h['version']}")
                    print(f"    文件: {h['pomFile']}")
                    all_hardcoded.append(h)

    print(f"\n共发现 {len(all_hardcoded)} 处写死版本")
    print("\n⚠️  这些版本需统一由 base-dependency 管理")

    output = Path(__file__).parent / "hardcoded_versions.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_hardcoded, f, ensure_ascii=False, indent=2)
    print(f"结果已保存: {output}")


if __name__ == "__main__":
    main()
