#!/usr/bin/env python3
"""替换 CI Python 代码中的二方件 import 为开源库"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CI_DIR = PROJECT_ROOT / "micrioservice-system" / "ci"

# import 替换映射
IMPORT_MAP = {
    # corp_ci_common
    "from corp_ci_common.logger import get_logger": "from loguru import logger",
    "from corp_ci_common.config_loader import ConfigLoader": "import yaml",
    "from corp_ci_common.git_utils import GitUtils": "import git",
    "from corp_ci_common.maven_utils import MavenUtils": "import subprocess",
    "from corp_ci_common.notify import NotificationSender": "import requests",
    # corp_ci_registry
    "from corp_ci_registry.docker_client import DockerClient": "import docker",
    "from corp_ci_registry.harbor_client import HarborClient": "import requests",
    "from corp_ci_registry.image_scanner import ImageScanner": "import subprocess",
}

# sys.path.insert 移除模式
SYS_PATH_PATTERN = re.compile(r"sys\.path\.insert\([^)]*2nd-components[^)]*\)")


def replace_in_file(py_file: Path):
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content

    # 移除 sys.path.insert 中的二方件路径
    content = SYS_PATH_PATTERN.sub("# 2nd-components 路径已移除（替换为开源库）", content)

    # 替换 import
    for old, new in IMPORT_MAP.items():
        content = content.replace(old, new)

    if content != original:
        py_file.write_text(content, encoding="utf-8")
        print(f"  已替换: {py_file.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("替换 CI Python import")
    print("=" * 70)
    total = sum(1 for py in CI_DIR.rglob("*.py") if replace_in_file(py))
    print(f"\n共修改 {total} 个 Python 文件")


if __name__ == "__main__":
    main()
