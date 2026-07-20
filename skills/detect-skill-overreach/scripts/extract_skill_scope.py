"""extract_skill_scope.py — 从目标 skill 的 SKILL.md 抽取声明的合法改动路径。

输出 JSON:
{
  "skill": "replace-corp-trace",
  "legal_paths": [
    "base-dependency/dependency-public/pom.xml",
    "base-framework/base-web/**",
    "base-framework/base-middleware/**",
    "user-module/**/pom.xml",
    "user-module/**/*.java",
    ...
  ],
  "warnings": []
}

合法路径解析规则:
- 目录形式("base-framework/base-web/") → "base-framework/base-web/**"
- 单文件形式("base-dependency/dependency-public/pom.xml") → 精确匹配
- "所有微服务的 pom.xml" → 展开为每个微服务模块的 pom.xml glob
- "所有微服务中使用 X 的 Java 文件" → 展开为每个微服务模块的 **/*.java glob
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4 :]
    return {}, body


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    cur_title: str | None = None
    cur_buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if cur_title is not None:
                sections[cur_title] = "\n".join(cur_buf).strip()
            cur_title = line[3:].strip()
            cur_buf = []
        elif line.startswith("### "):
            if cur_title is not None:
                cur_buf.append(line)
            else:
                cur_title = line[4:].strip()
                cur_buf = []
        else:
            if cur_title is not None:
                cur_buf.append(line)
    if cur_title is not None:
        sections[cur_title] = "\n".join(cur_buf).strip()
    return sections


def collect_scope_section(sections: dict[str, str]) -> tuple[str, str]:
    """优先匹配'影响范围'其次'处理范围''扫描范围'。"""
    for title in ("影响范围", "处理范围", "扫描范围"):
        for t, body in sections.items():
            if title in t:
                return body, t
    return "", ""


def normalize_scope_path(candidate: str) -> str:
    """把自然语言形式的影响范围行规范化为可展开的路径模式。

    处理:
    - "所有微服务中使用 TraceUtils/TraceContext 的 Java 文件" → "所有微服务/**/*.java"
    - "所有微服务的 pom.xml" → "所有微服务/**/pom.xml"
    - "所有微服务的 Java 文件" → "所有微服务/**/*.java"
    """
    s = candidate.strip()
    if "所有微服务" in s:
        if "java" in s.lower() or "Java" in s:
            return "所有微服务/**/*.java"
        if "pom" in s.lower():
            return "所有微服务/**/pom.xml"
        if "values.yaml" in s or "configmap" in s.lower() or "Chart.yaml" in s:
            return "所有微服务/**/values*.yaml"
        return "所有微服务/**"
    return s


def extract_path_candidates(scope_text: str) -> list[str]:
    """从范围文本抽路径候选行。"""
    paths: list[str] = []
    for line in scope_text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = re.sub(r"^\s*[-*]\s+", "", s)
        # 特殊处理:如果行里含"所有微服务",优先把"所有微服务"作为路径前缀
        # 反引号块只放文件类型,不丢失"所有微服务"上下文
        if "所有微服务" in s:
            # 取 — 之前的整段(保留"所有微服务"前缀)
            candidate = s.split("—")[0].strip().rstrip(":")
            candidate = normalize_scope_path(candidate)
            paths.append(candidate)
            continue
        m = re.search(r"`([^`]+)`", s)
        if m:
            candidate = m.group(1).strip()
        else:
            candidate = s.split("—")[0].strip().rstrip(":")
        candidate = normalize_scope_path(candidate)
        if "/" in candidate or "." in candidate or "所有微服务" in candidate:
            paths.append(candidate)
    return paths


def detect_microservice_modules(project_root: Path) -> list[str]:
    """识别微服务模块目录(与 base-* 同级且名字含 -module 的目录)。"""
    mods: list[str] = []
    for sub in project_root.iterdir():
        if not sub.is_dir():
            continue
        if sub.name.startswith(".") or sub.name.startswith("base-") or sub.name in ("ci", "2nd-components"):
            continue
        if "-module" in sub.name:
            mods.append(sub.name)
    return sorted(mods)


def to_glob(path: str, project_root: Path) -> list[str]:
    """把声明的路径解析为 git diff 可匹配的 glob。
    目录 → 目录/**
    文件 → 精确路径
    "所有微服务的 X" → 每个微服务模块/X
    """
    # 处理"所有微服务"
    if "所有微服务" in path:
        micro_mods = detect_microservice_modules(project_root)
        if not micro_mods:
            return [path]  # 无法展开,原样返回
        results: list[str] = []
        for mod in micro_mods:
            replaced = path.replace("所有微服务", mod)
            results.extend(to_glob(replaced, project_root))
        return results

    # 目录形式
    if path.endswith("/"):
        return [path + "**"]
    # 已经是 glob
    if "*" in path:
        return [path]
    # 单文件
    if "." in path.split("/")[-1]:
        return [path]
    # 既不是目录也不是文件,视为目录
    return [path + "/**"]


def main():
    ap = argparse.ArgumentParser(description="从目标 skill 抽取声明的合法改动路径")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--skills-root", default="skills")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    skill_md = Path(args.skills_root) / args.skill / "SKILL.md"
    if not skill_md.is_file():
        sys.stderr.write(f"skill not found: {skill_md}\n")
        sys.exit(1)

    text = skill_md.read_text(encoding="utf-8")
    _, body = parse_frontmatter(text)
    sections = parse_sections(body)

    scope_text, matched_title = collect_scope_section(sections)
    warnings: list[str] = []
    if not scope_text:
        warnings.append("影响范围小节缺失,所有改动都将视为越界")

    candidates = extract_path_candidates(scope_text)
    project_root = Path(args.project_root).resolve()
    legal_paths: list[str] = []
    for c in candidates:
        legal_paths.extend(to_glob(c, project_root))

    payload = {
        "skill": args.skill,
        "skill_md_path": str(skill_md),
        "scope_section_title": matched_title,
        "legal_paths": legal_paths,
        "warnings": warnings,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out} ({len(legal_paths)} paths)\n")


if __name__ == "__main__":
    main()
