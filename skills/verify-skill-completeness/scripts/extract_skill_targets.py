"""extract_skill_targets.py — 从目标 skill 的 SKILL.md 抽取声明的检查点。

检查点 = (路径, 文件类型, 指纹清单)
- 路径: 从"影响范围""处理范围""扫描范围"小节抽取
- 文件类型: 从路径中的扩展名或后缀识别(如 .java / pom.xml / ConfigMap)
- 指纹清单: 从"替换映射""处理规则"小节抽取旧 token(如 com.corp.trace、TraceUtils)

输出 JSON:
{
  "skill": "replace-corp-trace",
  "targets": [
    {"path": "base-dependency/dependency-public/pom.xml", "file_types": ["pom.xml"], "fingerprints": ["com.corp.trace", "corp-trace"]},
    {"path": "base-framework/base-web/", "file_types": ["java"], "fingerprints": ["com.corp.trace", "TraceUtils", "TraceContext"]},
    {"path": "所有微服务/*/pom.xml", "file_types": ["pom.xml"], "fingerprints": ["com.corp.trace", "corp-trace"]},
    {"path": "所有微服务/**/*.java", "file_types": ["java"], "fingerprints": ["TraceUtils", "TraceContext", "com.corp.trace"]}
  ],
  "warnings": ["影响范围小节缺失"]
}
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
    fm: dict = {}
    for line in fm_raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r'^([\w\-]+)\s*:\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip().strip("'\"")
            if val:
                fm[key] = val
    return fm, body


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
    """返回 (scope_text, matched_section_title)。容错:优先匹配'影响范围'其次'处理范围'再'扫描范围'。"""
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
    # 规则 1: "所有微服务" + "Java 文件" → 所有微服务/**/*.java
    if "所有微服务" in s:
        if "java" in s.lower() or "Java" in s:
            return "所有微服务/**/*.java"
        if "pom" in s.lower():
            return "所有微服务/**/pom.xml"
        if "values.yaml" in s or "configmap" in s.lower() or "Chart.yaml" in s:
            return "所有微服务/**/values*.yaml"
        # 默认展开所有微服务目录下所有文件
        return "所有微服务/**"
    return s


def extract_paths_from_scope(scope_text: str) -> list[str]:
    """从影响范围文本里抽路径行。
    识别形如:
      - `base-framework/base-web/` — xxx
      - `所有微服务的 pom.xml` — xxx
      - `所有微服务中使用 TraceUtils/TraceContext 的 Java 文件` — xxx
      - base-dependency/dependency-public/pom.xml
    """
    paths: list[str] = []
    for line in scope_text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # 去掉列表符号
        s = re.sub(r"^\s*[-*]\s+", "", s)
        # 特殊处理:如果行里含"所有微服务",优先把"所有微服务"作为路径前缀
        # 反引号块只放文件类型,不丢失"所有微服务"上下文
        if "所有微服务" in s:
            candidate = s.split("—")[0].strip().rstrip(":")
            candidate = normalize_scope_path(candidate)
            paths.append(candidate)
            continue
        # 提取第一个反引号块或第一段路径
        m = re.search(r"`([^`]+)`", s)
        if m:
            candidate = m.group(1).strip()
        else:
            # 取 — 之前的部分
            candidate = s.split("—")[0].strip().rstrip(":")
        # 规范化自然语言路径
        candidate = normalize_scope_path(candidate)
        # 过滤掉不像路径的(没有 / 也没有 . 也不含"所有微服务"的不要)
        if "/" in candidate or "." in candidate or "所有微服务" in candidate:
            paths.append(candidate)
    return paths


def infer_file_types(path: str) -> list[str]:
    """从路径推断文件类型。"""
    if path.endswith("pom.xml") or "/pom.xml" in path:
        return ["pom.xml"]
    if ".java" in path:
        return ["java"]
    if "values.yaml" in path or "configmap" in path.lower() or "Chart.yaml" in path:
        return ["yaml"]
    if ".py" in path:
        return ["python"]
    if path.endswith("/"):
        # 目录,默认扫所有类型,在 check 阶段再按指纹匹配
        return ["any"]
    return ["any"]


def extract_fingerprints(sections: dict[str, str], skill_name: str) -> list[str]:
    """从'替换映射''处理规则'小节抽取旧 token 作为残留指纹。

    指纹只保留明确的二方件 API/类名/包名,过滤掉:
    - 通用动词(clear/get/set/start/stop/next 等)
    - 太短的词(<=4 字符)
    - 带逗号/括号等标点的片段
    """
    # 通用动词/方法名黑名单:这些词太通用,作为指纹会大量误报
    COMMON_VERB_BLACKLIST = {
        "clear", "get", "set", "start", "stop", "next", "add", "remove",
        "create", "build", "run", "close", "refresh", "report",
        "increment", "record", "getCounter", "setGauge",
    }
    fps: set[str] = set()
    # 来源 1: 替换映射表(表格第一列)
    for title in ("替换映射", "处理规则", "配置项映射"):
        for t, body in sections.items():
            if title in t:
                for line in body.splitlines():
                    s = line.strip()
                    if s.startswith("|") and not s.startswith("|--") and not s.startswith("| -"):
                        # 表格行:取第一个单元格
                        cells = [c.strip() for c in s.split("|")]
                        cells = [c for c in cells if c]
                        if cells:
                            first = cells[0]
                            # 提取反引号块
                            m = re.search(r"`([^`]+)`", first)
                            if m:
                                token = m.group(1)
                                # 抽取类名/包名/方法名
                                for piece in re.split(r"[()\s]+", token):
                                    piece = piece.strip().rstrip(",")
                                    # 只保留: 长度>4 且不在黑名单 且不含逗号 且不以小写字母开头的通用词
                                    # (类名通常首字母大写,或 com.corp.xxx 包名)
                                    if not piece:
                                        continue
                                    if piece in COMMON_VERB_BLACKLIST:
                                        continue
                                    if len(piece) <= 4:
                                        continue
                                    # 必须是以下之一:
                                    # - 包名(com.corp.xxx)
                                    # - 类名(首字母大写,如 TraceUtils)
                                    # - 方法名但带特定前缀(getTraceId/getConfig 等)
                                    if piece.startswith("com.corp."):
                                        fps.add(piece)
                                    elif piece[0].isupper() and len(piece) >= 6:
                                        # 类名:TraceUtils / TraceContext / ConfigClient 等
                                        fps.add(piece)
                                    elif piece.startswith(("get", "set", "next", "start", "stop", "record")) and len(piece) > 8:
                                        # 特定方法名,要足够长避免误伤
                                        # 如 getTraceId(10 字符)保留,getDuration(11)保留
                                        # 但 getId(5)、set(3)、next(4)不保留
                                        fps.add(piece)
    # 来源 2: skill 名前缀(corp-* 类)
    if skill_name.startswith("replace-corp-"):
        comp_name = skill_name[len("replace-corp-") :]
        fps.add(f"com.corp.{comp_name.replace('-', '.')}")
        fps.add(f"corp-{comp_name}")
    # 来源 3: 职责范围文本里的 corp.xxx 包名
    duty = sections.get("职责范围", "")
    for m in re.finditer(r"com\.corp\.[\w.]+", duty):
        fps.add(m.group(0))
    for m in re.finditer(r"corp[_-][\w_-]+", duty):
        fps.add(m.group(0))
    # 过滤
    return sorted([f for f in fps if len(f) > 3 and f not in COMMON_VERB_BLACKLIST])


def expand_all_microservices(path: str, project_root: Path) -> list[str]:
    """把'所有微服务'展开为具体的微服务模块路径。"""
    if "所有微服务" not in path:
        return [path]
    # 识别微服务模块:与 base-* 同级,名字含 -module 或 -service 的目录
    micro_modules: list[str] = []
    for sub in project_root.iterdir():
        if not sub.is_dir():
            continue
        if sub.name.startswith(".") or sub.name.startswith("base-") or sub.name in ("ci", "2nd-components"):
            continue
        # 含 -module 的视为微服务模块
        if "-module" in sub.name:
            micro_modules.append(sub.name)
    # 替换"所有微服务"为每个微服务模块
    expanded: list[str] = []
    for mod in micro_modules:
        expanded.append(path.replace("所有微服务", mod))
    return expanded if expanded else [path]


def main():
    ap = argparse.ArgumentParser(description="从目标 skill 的 SKILL.md 抽取检查点")
    ap.add_argument("--skill", required=True, help="目标 skill 名(目录名)")
    ap.add_argument("--skills-root", default="skills", help="skills 目录")
    ap.add_argument("--project-root", default=".", help="项目根目录(用于展开'所有微服务')")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    skill_md = Path(args.skills_root) / args.skill / "SKILL.md"
    if not skill_md.is_file():
        sys.stderr.write(f"skill not found: {skill_md}\n")
        sys.exit(1)

    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)

    scope_text, matched_title = collect_scope_section(sections)
    warnings: list[str] = []
    if not scope_text:
        warnings.append("影响范围小节缺失,无法抽取检查点")

    paths = extract_paths_from_scope(scope_text)
    fingerprints = extract_fingerprints(sections, args.skill)

    # 展开所有微服务
    project_root = Path(args.project_root).resolve()
    expanded_paths: list[str] = []
    for p in paths:
        expanded_paths.extend(expand_all_microservices(p, project_root))

    targets = [
        {"path": p, "file_types": infer_file_types(p), "fingerprints": fingerprints}
        for p in expanded_paths
    ]

    payload = {
        "skill": args.skill,
        "skill_md_path": str(skill_md),
        "scope_section_title": matched_title,
        "targets": targets,
        "warnings": warnings,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out} ({len(targets)} targets)\n")


if __name__ == "__main__":
    main()
