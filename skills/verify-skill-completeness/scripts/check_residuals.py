"""check_residuals.py — 对检查点执行 Grep 扫描,输出残留清单。

输入: extract_skill_targets.py 的 JSON 输出 + 项目根目录
逻辑: 对每个 target,在其 path 下扫描 fingerprints 的残留
输出: Markdown 报告
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_ripgrep(pattern: str, path: str, project_root: Path) -> list[tuple[str, int, str]]:
    """调用 rg 扫描。返回 [(文件, 行号, 命中行), ...]"""
    target_path = (project_root / path).resolve() if not Path(path).is_absolute() else Path(path)
    if not target_path.exists():
        # 可能路径本身是一个 glob,直接交给 rg
        target_path = project_root / path
    try:
        result = subprocess.run(
            ["rg", "-n", "--no-heading", "-e", pattern, str(target_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        # rg 不存在,降级 grep
        result = subprocess.run(
            ["grep", "-rn", "-e", pattern, str(target_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return []
    hits: list[tuple[str, int, str]] = []
    for line in result.stdout.splitlines():
        # 格式: 文件:行号:内容 或 文件:内容(grep 无行号)
        parts = line.split(":", 2)
        if len(parts) >= 3:
            try:
                lineno = int(parts[1])
            except ValueError:
                continue
            hits.append((parts[0], lineno, parts[2].strip()))
    return hits


def check_one_target(target: dict, project_root: Path) -> dict:
    """对单个 target 执行扫描。返回 {path, file_types, fingerprints, residuals: [...]}"""
    path = target["path"]
    fps = target["fingerprints"]
    if not fps:
        return {
            "path": path,
            "file_types": target["file_types"],
            "fingerprints": fps,
            "residuals": [],
            "note": "无指纹清单,跳过扫描",
        }
    residuals: list[dict] = []
    for fp in fps:
        hits = run_ripgrep(fp, path, project_root)
        for fpath, lineno, content in hits[:5]:  # 每个指纹最多报 5 条
            rel_path = str(Path(fpath).relative_to(project_root)) if project_root in Path(fpath).parents or Path(fpath).relative_to(project_root) else fpath
            residuals.append(
                {"fingerprint": fp, "file": rel_path, "line": lineno, "content": content}
            )
    return {
        "path": path,
        "file_types": target["file_types"],
        "fingerprints": fps,
        "residuals": residuals,
        "note": "" if residuals else "无残留",
    }


def render_report(skill: str, results: list[dict], warnings: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"## verify-skill-completeness 报告:{skill}")
    lines.append("")
    if warnings:
        lines.append("### 声明缺失提示")
        for w in warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    lines.append("### 声明检查点(来自 SKILL.md 影响范围)")
    for i, r in enumerate(results, 1):
        fps = ", ".join(r["fingerprints"]) if r["fingerprints"] else "(无指纹)"
        lines.append(f"{i}. {r['path']} — 指纹: {fps}")
    lines.append("")

    lines.append("### 扫描结果")
    ok_count = 0
    bad_count = 0
    for i, r in enumerate(results, 1):
        if r["residuals"]:
            bad_count += 1
            lines.append(f"{i}. ❌ {r['path']}")
            for res in r["residuals"]:
                lines.append(
                    f"   - 残留: `{res['content'][:80]}` @ {res['file']}:{res['line']} (匹配 {res['fingerprint']})"
                )
        else:
            ok_count += 1
            note = r.get("note", "")
            lines.append(f"{i}. ✅ {r['path']} — {note}")

    lines.append("")
    if bad_count == 0:
        lines.append(f"### 汇总结论: ✅ 完整(所有 {ok_count} 个检查点无残留)")
    else:
        lines.append(f"### 汇总结论: ❌ 有遗漏")
        lines.append(f"- 残留检查点数: {bad_count} / {len(results)}")
        lines.append(f"- 需要回看 {skill} 的执行,补改遗漏的 {bad_count} 处")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="对检查点执行 Grep 扫描,检测残留")
    ap.add_argument("--targets", required=True, help="extract_skill_targets.py 的 JSON 输出路径")
    ap.add_argument("--project-root", default=".", help="项目根目录")
    ap.add_argument("--out", default="-", help="输出报告路径,- 表示 stdout")
    args = ap.parse_args()

    data = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    project_root = Path(args.project_root).resolve()
    results = [check_one_target(t, project_root) for t in data["targets"]]
    report = render_report(data["skill"], results, data.get("warnings", []))

    if args.out == "-":
        print(report)
    else:
        Path(args.out).write_text(report, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
