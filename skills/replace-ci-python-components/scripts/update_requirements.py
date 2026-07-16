#!/usr/bin/env python3
"""更新 requirements.txt：移除 corp 二方件，添加开源库"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CI_DIR = PROJECT_ROOT / "micrioservice-system" / "ci"

# 需要移除的二方件
REMOVE_PACKAGES = ["corp-ci-common", "corp-ci-registry"]

# 需要添加的开源库
ADD_PACKAGES = [
    "loguru>=0.7.0",
    "pyyaml>=6.0",
    "gitpython>=3.1.0",
    "docker>=6.1.0",
    "requests>=2.31.0",
]


def update_requirements(req_file: Path):
    if not req_file.exists():
        return False

    content = req_file.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 移除 corp 二方件
    new_lines = [l for l in lines if not any(pkg in l.lower() for pkg in REMOVE_PACKAGES)]

    # 添加开源库（如果不存在）
    existing = set(l.lower().split("==")[0].split(">=")[0].split("<")[0].strip() for l in new_lines)
    for pkg in ADD_PACKAGES:
        pkg_name = pkg.split(">=")[0].split("<")[0].strip()
        if pkg_name not in existing:
            new_lines.append(pkg)

    new_content = "\n".join(new_lines) + "\n"
    if new_content != content:
        req_file.write_text(new_content, encoding="utf-8")
        print(f"  已更新: {req_file.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("更新 requirements.txt")
    print("=" * 70)
    for req in CI_DIR.rglob("requirements.txt"):
        update_requirements(req)


if __name__ == "__main__":
    main()
