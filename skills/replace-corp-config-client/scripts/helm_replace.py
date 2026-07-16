#!/usr/bin/env python3
"""修改 Helm Chart ConfigMap：添加 spring.cloud.config 配置"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

CHART_DIRS = [
    MICROSERVICE_DIR / "user-module" / "user-module-chart",
    MICROSERVICE_DIR / "order-module" / "order-module-chart",
    MICROSERVICE_DIR / "product-module" / "product-module-chart",
]

SCC_CONFIG_BLOCK = """
    <spring-cloud-config>
        <uri>http://config-server.config-server.svc.cluster.local:8888</uri>
        <label>main</label>
        <profile>{{ .Values.global.env | default "prod" }}</profile>
        <fail-fast>true</fail-fast>
    </spring-cloud-config>"""


def update_configmap(chart_dir: Path):
    """在 app-configmap 的 application.xml 中添加 spring-cloud-config 配置块"""
    templates = chart_dir / "templates"
    if not templates.exists():
        return

    for cm in templates.glob("*-app-configmap.yaml"):
        content = cm.read_text(encoding="utf-8")
        if "spring-cloud-config" in content:
            print(f"  已存在配置: {cm.name}")
            continue

        # 在 </config> 前插入
        content = content.replace("</config>", SCC_CONFIG_BLOCK + "\n    </config>")
        cm.write_text(content, encoding="utf-8")
        print(f"  添加 SCC 配置: {cm.relative_to(PROJECT_ROOT)}")


def main():
    print("=" * 70)
    print("Helm ConfigMap 修改: 添加 spring-cloud-config")
    print("=" * 70)
    for chart_dir in CHART_DIRS:
        if chart_dir.exists():
            print(f"\n[{chart_dir.name}]")
            update_configmap(chart_dir)


if __name__ == "__main__":
    main()
