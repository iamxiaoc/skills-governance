#!/usr/bin/env python3
"""改写 CI Python 代码逻辑：适配开源库的 API 调用方式"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CI_DIR = PROJECT_ROOT / "micrioservice-system" / "ci"

# 代码逻辑替换规则
CODE_REPLACEMENTS = [
    # logger
    (re.compile(r'get_logger\("(\w+)"\)'), 'logger'),
    (re.compile(r'logger\.step\("(\w+)"\)\.info'), 'logger.info'),
    (re.compile(r'logger\.success'), 'logger.success'),
    (re.compile(r'logger\.fail'), 'logger.error'),
    (re.compile(r'logger\.info'), 'logger.info'),
    # ConfigLoader
    (re.compile(r'ConfigLoader\(([^)]+)\)'), r'open(\1)'),
    (re.compile(r'config\.load\(\)'), 'config = yaml.safe_load(config_file)'),
    (re.compile(r'config\.get\("([\w.]+)"(?:,\s*([^)]+))?\)'),
     lambda m: f'config.get("{m.group(1)}"' + (f', {m.group(2)}' if m.group(2) else '') + ')'),
    # GitUtils
    (re.compile(r'GitUtils\(([^)]+)\)'), r'git.Repo(\1)'),
    (re.compile(r'git\.get_current_branch\(\)'), 'git.active_branch.name'),
    (re.compile(r'git\.get_commit_id\(\)'), 'git.head.commit.hexsha'),
    (re.compile(r'git\.get_commit_message\(\)'), 'git.head.commit.message'),
    # NotificationSender
    (re.compile(r'NotificationSender\(([^,]+),\s*([^)]+)\)'),
     r'{"url": \1, "type": \2}'),
    (re.compile(r'notifier\.notify\(([^,]+),\s*([^)]+)\)'),
     r'requests.post(notifier["url"], json={"title": \1, "content": \2})'),
]


def rewrite_file(py_file: Path):
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content
    for pattern, replacement in CODE_REPLACEMENTS:
        content = pattern.sub(replacement, content)

    if content != original:
        py_file.write_text(content, encoding="utf-8")
        print(f"  已改写: {py_file.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("改写 CI Python 代码逻辑")
    print("=" * 70)
    total = sum(1 for py in CI_DIR.rglob("*.py") if rewrite_file(py))
    print(f"\n共修改 {total} 个 Python 文件")
    print("\n⚠️  API 调用方式变化较大，需人工检查")


if __name__ == "__main__":
    main()
