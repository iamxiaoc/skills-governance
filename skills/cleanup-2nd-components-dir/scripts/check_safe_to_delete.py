#!/usr/bin/env python3
"""检查某个二方件是否可以安全删除（无残留引用）"""

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "microservice-system"

COMPONENT_MAP = {
    "corp-trace": "com.corp.trace",
    "corp-id-generator": "com.corp.id",
    "corp-config-client": "com.corp.config",
    "corp-monitor": "com.corp.monitor",
    "corp-ci-common": "corp_ci_common",
    "corp-ci-registry": "corp_ci_registry",
}


def check_references(component: str):
    """检查项目中是否还有该二方件的残留引用"""
    pkg = COMPONENT_MAP.get(component)
    if not pkg:
        print(f"未知二方件: {component}")
        print(f"支持: {', '.join(COMPONENT_MAP.keys())}")
        return False

    refs_found = []

    # 扫描 Java 文件（排除 2nd-components 自身）
    for java in MICROSERVICE_DIR.rglob("*.java"):
        if "2nd-components" in str(java):
            continue
        try:
            content = java.read_text(encoding="utf-8")
            if pkg in content:
                refs_found.append(("Java", str(java.relative_to(PROJECT_ROOT))))
        except Exception:
            pass

    # 扫描 pom.xml
    for pom in MICROSERVICE_DIR.rglob("pom.xml"):
        if "2nd-components" in str(pom):
            continue
        try:
            content = pom.read_text(encoding="utf-8")
            if pkg in content:
                refs_found.append(("pom.xml", str(pom.relative_to(PROJECT_ROOT))))
        except Exception:
            pass

    # 扫描 Python 文件
    for py in MICROSERVICE_DIR.rglob("*.py"):
        if "2nd-components" in str(py):
            continue
        try:
            content = py.read_text(encoding="utf-8")
            if pkg in content:
                refs_found.append(("Python", str(py.relative_to(PROJECT_ROOT))))
        except Exception:
            pass

    # 扫描 ConfigMap
    for cm in MICROSERVICE_DIR.rglob("*-configmap.yaml"):
        try:
            content = cm.read_text(encoding="utf-8")
            if component in content:
                refs_found.append(("ConfigMap", str(cm.relative_to(PROJECT_ROOT))))
        except Exception:
            pass

    if refs_found:
        print(f"❌ {component} 仍有残留引用，不可安全删除:")
        for typ, path in refs_found:
            print(f"  [{typ}] {path}")
        return False
    else:
        print(f"✅ {component} 无残留引用，可以安全删除")
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", required=True, choices=list(COMPONENT_MAP.keys()))
    args = parser.parse_args()
    safe = check_references(args.component)
    exit(0 if safe else 1)


if __name__ == "__main__":
    main()
