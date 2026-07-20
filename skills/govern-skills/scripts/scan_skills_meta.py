"""scan_skills_meta.py — 扫描 skills 目录,为每个 skill 收集元信息。

输出 JSON 数组,每个元素描述一个 skill:
{
  "name": "replace-corp-trace",
  "skill_md_path": "skills/replace-corp-trace/SKILL.md",
  "frontmatter": {"name": "...", "description": "...", "tags": [...] (若已有), ...},
  "sections": {"职责范围": "...", "影响范围": "...", ...},  # 按小节标题归集原文
  "script_files": ["scripts/maven_replace.py", ...],
  "scope_raw_snippets": ["所有微服务中使用 TraceUtils 的 Java 文件", ...],  # 影响范围原文片段
  "trigger_raw_snippets": ["在替换某个二方件前...", ...],  # 触发场景原文片段
}

容错策略:
- 缺失 frontmatter: 返回 frontmatter={}
- 缺失某些小节: 对应 sections 键不存在,不报错
- 小节标题措辞不一: 用前缀/包含匹配,如"职责范围""职责""影响范围""处理范围""扫描范围"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# 关注的小节标题关键字(包含匹配,非全等)
SECTION_KEYWORDS = {
    "职责": "职责",
    "范围": "范围",  # 含"职责范围""影响范围""处理范围""扫描范围"
    "触发": "触发",
    "前置条件": "前置条件",
    "执行步骤": "执行步骤",
    "替换映射": "替换映射",
    "处理规则": "处理规则",
    "对比策略": "对比策略",
    "验证方法": "验证方法",
    "约束": "约束",
    "输出格式": "输出格式",
    "设计原则": "设计原则",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML frontmatter。容错:缺失则返回空 dict。"""
    if not text.startswith("---"):
        return {}, text
    # 找第二个 ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    # 极简 YAML 解析:只认 key: value 和 key: [list] 和多行 list
    fm: dict = {}
    cur_key: str | None = None
    for line in fm_raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r'^([\w\-]+)\s*:\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            cur_key = key
            if val:
                # 单行值:可能是 "xxx" 或 [a, b] 或 "a"
                if val.startswith("[") and val.endswith("]"):
                    inner = val[1:-1].strip()
                    fm[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
                else:
                    fm[key] = val.strip("'\"")
            else:
                fm[key] = []  # 多行 list 占位
        elif cur_key and line.lstrip().startswith("-"):
            item = line.lstrip()[1:].strip().strip("'\"")
            if isinstance(fm.get(cur_key), list):
                fm[cur_key].append(item)
    return fm, body


def parse_sections(body: str) -> dict:
    """按二级标题(## ...)切分小节,返回 {标题: 正文}。
    兼容三级标题(###)作为子小节并入最近的二级标题。
    """
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
            # 三级标题作为子小节并入当前二级
            if cur_title is not None:
                cur_buf.append(line)
            else:
                cur_title = line[4:].strip()
                cur_buf = []
        else:
            if cur_title is not None:
                cur_buf.append(line)
            # 标题前正文丢弃
    if cur_title is not None:
        sections[cur_title] = "\n".join(cur_buf).strip()
    return sections


def collect_sections_by_keyword(sections: dict[str, str]) -> dict[str, str]:
    """按 SECTION_KEYWORDS 把小节归集到标准桶。"""
    out: dict[str, str] = {}
    for title, body in sections.items():
        for canon, kw in SECTION_KEYWORDS.items():
            if kw in title:
                # 合并:同桶多个小节用 \n---\n 分隔
                if canon in out:
                    out[canon] = out[canon] + "\n---\n" + title + ":\n" + body
                else:
                    out[canon] = title + ":\n" + body
    return out


def collect_raw_snippets(section_text: str, max_lines: int = 20) -> list[str]:
    """从一个小节文本里抽取"看起来像影响范围/触发场景"的原文行。"""
    if not section_text:
        return []
    snippets: list[str] = []
    # 优先抽 bullet 行
    for line in section_text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # 去掉 markdown 列表符号和表格符号
        s = re.sub(r"^\s*[-*]\s+", "", s)
        s = re.sub(r"^\s*\d+\.\s+", "", s)
        s = s.strip("`| ")
        if s and len(s) > 4:
            snippets.append(s)
        if len(snippets) >= max_lines:
            break
    return snippets


def collect_script_files(skill_dir: Path) -> list[str]:
    """收集 skill 目录下 scripts/ 中的 .py 文件(相对路径)。"""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return []
    result: list[str] = []
    for p in sorted(scripts_dir.rglob("*.py")):
        result.append(str(p.relative_to(skill_dir)))
    return result


def scan_one_skill(skill_dir: Path, root: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return {}
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)
    grouped = collect_sections_by_keyword(sections)

    # 影响范围原文片段:从"范围"桶抽
    scope_snippets = collect_raw_snippets(grouped.get("范围", ""))
    # 触发场景原文片段:从"触发"和"前置条件"桶抽
    trigger_snippets = collect_raw_snippets(grouped.get("触发", "")) + collect_raw_snippets(
        grouped.get("前置条件", "")
    )
    # 执行步骤原文片段:从"执行步骤"桶抽
    steps_snippets = collect_raw_snippets(grouped.get("执行步骤", ""))

    return {
        "name": skill_dir.name,
        "skill_md_path": str(skill_md.relative_to(root)),
        "frontmatter": fm,
        "sections": grouped,
        "script_files": collect_script_files(skill_dir),
        "scope_raw_snippets": scope_snippets,
        "trigger_raw_snippets": trigger_snippets,
        "steps_raw_snippets": steps_snippets,
    }


def main():
    ap = argparse.ArgumentParser(description="扫描 skills 目录,收集每个 skill 的元信息")
    ap.add_argument(
        "--skills-root",
        default="skills",
        help="skills 目录(默认: skills)",
    )
    ap.add_argument("--out", default="-", help="输出 JSON 路径,- 表示 stdout")
    args = ap.parse_args()

    root = Path(args.skills_root).resolve()
    if not root.is_dir():
        sys.stderr.write(f"skills dir not found: {root}\n")
        sys.exit(1)

    skills: list[dict] = []
    for sub in sorted(root.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name.startswith("."):
            continue
        if not (sub / "SKILL.md").is_file():
            continue
        info = scan_one_skill(sub, root.parent)
        if info:
            skills.append(info)

    payload = {"skills_root": str(root), "count": len(skills), "skills": skills}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out} ({len(skills)} skills)\n")


if __name__ == "__main__":
    main()
