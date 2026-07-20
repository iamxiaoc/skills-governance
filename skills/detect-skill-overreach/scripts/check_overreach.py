"""check_overreach.py — 对照声明的合法路径,检查 git diff 是否越界。

输入:
- extract_skill_scope.py 的 JSON 输出
- skill 执行前的 git commit SHA(或省略,走未提交改动)

逻辑:
1. 拿 git diff 文件清单
2. 对每个改动文件,判断是否落在任一 legal_path 之内
3. 落在外面的,记为越界
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path


def get_changed_files(before_sha: str | None, project_root: Path) -> list[tuple[str, str]]:
    """返回 [(文件路径, 状态:A/M/D), ...]。
    传 before_sha 走 git diff <sha>..HEAD,否则走 git diff HEAD(未提交改动)。
    在 project_root 目录里跑 git,这样输出路径是相对 project_root 的。
    """
    if before_sha:
        cmd = ["git", "diff", "--name-status", f"{before_sha}..HEAD"]
    else:
        cmd = ["git", "diff", "--name-status", "HEAD"]
    # 如果 project_root 不是 git 仓根,git 会自动向上找 .git,但输出路径仍相对 git 仓根
    # 为了让输出相对 project_root,加 --relative 参数
    cmd.append("--relative")
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(project_root), timeout=60
    )
    files: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0].strip()[:1]  # A / M / D / R(ename) 只取首字母
        fpath = parts[-1].strip()
        files.append((fpath, status))
    return files


def path_matches_legal(path: str, legal_path: str) -> bool:
    """判断 path 是否落在 legal_path 之内。"""
    # legal_path 形如:
    # - "base-framework/base-web/**" → 目录下任意
    # - "base-dependency/dependency-public/pom.xml" → 精确
    # - "user-module/**/*.java" → glob
    # - "user-module/**/pom.xml" → glob
    if legal_path.endswith("/**"):
        prefix = legal_path[:-3]
        return path.startswith(prefix)
    if "*" in legal_path:
        return fnmatch.fnmatch(path, legal_path)
    return path == legal_path


def is_legal(path: str, legal_paths: list[str]) -> tuple[bool, str | None]:
    """返回 (是否合法, 匹配的 legal_path)。"""
    for lp in legal_paths:
        if path_matches_legal(path, lp):
            return True, lp
    return False, None


def get_diff_stat(path: str, before_sha: str | None, project_root: Path) -> str:
    """拿单个文件的 +/- 行数。"""
    if before_sha:
        cmd = ["git", "diff", "--numstat", f"{before_sha}..HEAD", "--relative", "--", path]
    else:
        cmd = ["git", "diff", "--numstat", "HEAD", "--relative", "--", path]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(project_root), timeout=30
    )
    line = result.stdout.strip()
    if not line:
        return "?"
    parts = line.split()
    if len(parts) >= 2:
        return f"+{parts[0]} -{parts[1]}"
    return "?"


def render_report(
    skill: str,
    before_sha: str | None,
    changed: list[tuple[str, str]],
    legal_paths: list[str],
    overreaches: list[dict],
    warnings: list[str],
) -> str:
    lines: list[str] = []
    lines.append(f"## detect-skill-overreach 报告:{skill}")
    baseline_desc = before_sha if before_sha else "未提交改动(HEAD)"
    lines.append(f"- 基线: {baseline_desc}")
    lines.append(f"- 改动文件总数: {len(changed)}")
    lines.append(f"- 合法改动: {len(changed) - len(overreaches)} (落在声明影响范围内)")
    lines.append(f"- 越界改动: {len(overreaches)}")
    lines.append("")

    if warnings:
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    if not overreaches:
        lines.append("### 汇总结论: ✅ 无越界")
        return "\n".join(lines)

    lines.append("### 越界清单")
    for i, ov in enumerate(overreaches, 1):
        lines.append(f"{i}. {ov['path']}")
        lines.append(f"   - 改动: {ov['stat']}")
        lines.append(f"   - 原因: 不在声明的'影响范围'内")
    lines.append("")
    lines.append(f"### 汇总结论: ❌ 有越界")
    lines.append(f"- 需要人工确认以下 {len(overreaches)} 个文件的改动是否必要:")
    for ov in overreaches:
        lines.append(f"  - {ov['path']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="对照声明的合法路径,检查 git diff 是否越界")
    ap.add_argument("--scope", required=True, help="extract_skill_scope.py 的 JSON 输出路径")
    ap.add_argument("--before-sha", default="", help="skill 执行前的 git commit SHA,省略则走未提交改动")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    data = json.loads(Path(args.scope).read_text(encoding="utf-8"))
    project_root = Path(args.project_root).resolve()
    legal_paths = data.get("legal_paths", [])
    warnings = data.get("warnings", [])

    before_sha = args.before_sha or None
    changed = get_changed_files(before_sha, project_root)

    overreaches: list[dict] = []
    for fpath, _status in changed:
        ok, _ = is_legal(fpath, legal_paths)
        if not ok:
            stat = get_diff_stat(fpath, before_sha, project_root)
            overreaches.append({"path": fpath, "stat": stat})

    report = render_report(
        data["skill"], before_sha, changed, legal_paths, overreaches, warnings
    )
    if args.out == "-":
        print(report)
    else:
        Path(args.out).write_text(report, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
