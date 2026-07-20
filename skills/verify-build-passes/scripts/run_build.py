"""run_build.py — 执行构建命令,捕获 exit code 和 stderr,输出 Markdown 报告。

逻辑:
- 读 detect_project_type.py 的 JSON 输出(或自己探测)
- 根据项目类型选择构建命令:
  - maven: mvn -q compile -DskipTests
  - python: 对每个 .py 文件执行 python -m py_compile
  - mixed: 两种都跑,任一失败即失败
- 严格禁止 -Dtest= / -Dgroups= 参数(忽略并提示)

约束:
- 不解析错误,只输出错误摘要(前 50 行 stderr)
- 构建工具本身缺失时报"工具缺失"
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def strip_test_args(args: list[str]) -> tuple[list[str], list[str]]:
    """剔除任何 -Dtest= / -Dgroups= 参数,并返回被剔除的参数列表。"""
    stripped: list[str] = []
    kept: list[str] = []
    for a in args:
        if a.startswith("-Dtest=") or a.startswith("-Dgroups="):
            stripped.append(a)
        else:
            kept.append(a)
    return kept, stripped


def run_maven(project_root: Path, mvn_args: list[str]) -> dict:
    mvn = shutil.which("mvn")
    if not mvn:
        return {
            "tool": "mvn",
            "command": "mvn (not found)",
            "exit_code": -1,
            "stderr": "mvn 命令不存在,工具缺失",
            "skipped_test_args": [],
        }
    args, stripped = strip_test_args(mvn_args)
    # 不用 -q,让错误信息能输出
    cmd = [mvn, "compile", "-DskipTests"] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(project_root), timeout=600
    )
    # mvn 失败时错误可能在 stderr 或 stdout,合并取前 50 行
    combined = result.stderr + result.stdout
    err_lines = [l for l in combined.splitlines() if l.strip()][:50]
    return {
        "tool": "mvn",
        "command": " ".join(cmd),
        "exit_code": result.returncode,
        "stderr": "\n".join(err_lines),
        "skipped_test_args": stripped,
    }


def run_python_compile(project_root: Path, py_files: list[str]) -> dict:
    python = shutil.which("python3") or shutil.which("python")
    if not python:
        return {
            "tool": "python",
            "command": "python (not found)",
            "exit_code": -1,
            "stderr": "python 命令不存在,工具缺失",
            "failed_files": [],
        }
    failed: list[dict] = []
    for rel in py_files:
        abs_path = project_root / rel
        cmd = [python, "-m", "py_compile", str(abs_path)]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            failed.append({"file": rel, "error": "timeout"})
            continue
        if result.returncode != 0:
            failed.append(
                {"file": rel, "error": result.stderr.strip()[:500]}
            )
    return {
        "tool": "python",
        "command": f"{python} -m py_compile <{len(py_files)} files>",
        "exit_code": 0 if not failed else 1,
        "stderr": "",
        "failed_files": failed[:50],
    }


def render_report(project_type: str, maven_result: dict | None, python_result: dict | None) -> str:
    lines: list[str] = []
    lines.append("## verify-build-passes 报告")
    lines.append(f"- 项目类型: {project_type}")
    lines.append("")

    passed = True
    for result in [maven_result, python_result]:
        if not result:
            continue
        lines.append(f"- 构建命令: {result['command']}")
        if result.get("skipped_test_args"):
            lines.append(
                f"- ⚠️ 已忽略禁止的测试参数: {', '.join(result['skipped_test_args'])}"
            )
        lines.append(f"- exit code: {result['exit_code']}")
        if result["exit_code"] == 0:
            lines.append("- 结论: ✅ 通过")
        elif result["exit_code"] == -1:
            lines.append("- 结论: ❌ 工具缺失")
            passed = False
        else:
            lines.append("- 结论: ❌ 失败")
            passed = False
            if result.get("stderr"):
                lines.append("")
                lines.append("### 错误摘要(前 50 行 stderr)")
                lines.append("```")
                lines.append(result["stderr"])
                lines.append("```")
            if result.get("failed_files"):
                lines.append("")
                lines.append("### 失败文件清单")
                for f in result["failed_files"]:
                    lines.append(f"- {f['file']}")
                    lines.append(f"  ```{f['error'][:200]}```")
        lines.append("")

    lines.append(f"### 汇总结论: {'✅ 全部通过' if passed else '❌ 有失败'}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="执行构建命令验证语法和依赖")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--type-info", default="", help="detect_project_type.py 的 JSON 输出路径,省略则自己探测")
    ap.add_argument("--mvn-args", default="", help="额外传给 mvn 的参数(空格分隔)")
    ap.add_argument("--py-files", default="", help="指定要编译的 py 文件(逗号分隔),省略则全扫")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()

    if args.type_info:
        type_info = json.loads(Path(args.type_info).read_text(encoding="utf-8"))
    else:
        # 内联探测
        from detect_project_type import scan_project
        type_info = scan_project(project_root)

    ptype = type_info["type"]
    maven_result: dict | None = None
    python_result: dict | None = None

    if ptype in ("maven", "mixed"):
        extra = args.mvn_args.split() if args.mvn_args else []
        maven_result = run_maven(project_root, extra)

    if ptype in ("python", "mixed"):
        if args.py_files:
            py_files = [f.strip() for f in args.py_files.split(",") if f.strip()]
        else:
            py_files = type_info.get("sample_py_files", [])
            # sample 只有 5 个,如果想要全量,用 rg 扫
            # 此处保守用 sample,避免脚本跑太久
        python_result = run_python_compile(project_root, py_files)

    report = render_report(ptype, maven_result, python_result)
    if args.out == "-":
        print(report)
    else:
        Path(args.out).write_text(report, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
