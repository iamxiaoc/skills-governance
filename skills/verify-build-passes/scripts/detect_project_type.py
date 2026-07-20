"""detect_project_type.py — 探测项目类型(Maven / Python / 混合)。

逻辑:
- 递归扫项目根目录,统计 pom.xml 和 *.py 的分布
- 有 pom.xml → Maven 项目
- 有 *.py 但无 pom.xml → Python 项目
- 两者都有 → 混合项目

输出 JSON:
{
  "project_root": "/abs/path",
  "type": "maven" | "python" | "mixed",
  "maven_pom_count": N,
  "python_file_count": N,
  "sample_pom_files": ["base-dependency/pom.xml", ...],
  "sample_py_files": ["ci/build-pipeline/main.py", ...]
}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def scan_project(project_root: Path) -> dict:
    pom_files: list[str] = []
    py_files: list[str] = []
    # 排除一些目录避免误判
    ignore_dirs = {".git", "target", "node_modules", ".vscode", ".idea", "__pycache__"}
    for p in project_root.rglob("*"):
        if not p.is_file():
            continue
        # 路径里任一段在 ignore_dirs 就跳过
        try:
            rel = p.relative_to(project_root)
        except ValueError:
            continue
        if any(part in ignore_dirs for part in rel.parts):
            continue
        if p.name == "pom.xml":
            pom_files.append(str(rel))
        elif p.suffix == ".py":
            py_files.append(str(rel))
    pom_count = len(pom_files)
    py_count = len(py_files)
    if pom_count > 0 and py_count > 0:
        ptype = "mixed"
    elif pom_count > 0:
        ptype = "maven"
    elif py_count > 0:
        ptype = "python"
    else:
        ptype = "unknown"
    return {
        "project_root": str(project_root),
        "type": ptype,
        "maven_pom_count": pom_count,
        "python_file_count": py_count,
        "sample_pom_files": sorted(pom_files)[:5],
        "sample_py_files": sorted(py_files)[:5],
    }


def main():
    ap = argparse.ArgumentParser(description="探测项目类型")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        sys.stderr.write(f"project root not found: {project_root}\n")
        sys.exit(1)

    result = scan_project(project_root)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out}\n")


if __name__ == "__main__":
    main()
