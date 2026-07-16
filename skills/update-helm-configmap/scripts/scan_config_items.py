#!/usr/bin/env python3
"""扫描所有 ConfigMap 中的旧配置项"""

from pathlib import Path
import re
import json

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

OLD_CONFIG_PATTERNS = [
    (r"corp-trace", "trace"),
    (r"corp-config", "config-center"),
    (r"corp-monitor", "monitor"),
    (r"corp-id-generator|corp\.id\.IdGenerator", "id-generator"),
]


def scan_configmap(cm_path: Path):
    content = cm_path.read_text(encoding="utf-8")
    findings = []
    for pattern, category in OLD_CONFIG_PATTERNS:
        for match in re.finditer(pattern, content):
            # 找到所在行
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end].strip()
            findings.append({
                "file": str(cm_path.relative_to(PROJECT_ROOT)),
                "category": category,
                "line": line,
            })
    return findings


def main():
    print("=" * 70)
    print("扫描 ConfigMap 旧配置项")
    print("=" * 70)

    all_findings = []
    for chart_dir in CHART_DIRS:
        if not chart_dir.exists():
            continue
        templates = chart_dir / "templates"
        if not templates.exists():
            continue
        for cm in templates.glob("*-configmap.yaml"):
            findings = scan_configmap(cm)
            if findings:
                print(f"\n[{cm.relative_to(PROJECT_ROOT)}]")
                for f in findings:
                    print(f"  [{f['category']}] {f['line']}")
            all_findings.extend(findings)

    print(f"\n共发现 {len(all_findings)} 处旧配置项")
    output = Path(__file__).parent / "old_config_items.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_findings, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
