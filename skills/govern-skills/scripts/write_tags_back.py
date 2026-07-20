"""write_tags_back.py — 将最终标签写回各 SKILL.md 的 frontmatter。

约束:
- 若 frontmatter 中已存在 tags / category 字段,保留人工修订值,不覆盖
- 仅在缺失时补写
- 不修改业务代码,只触碰 SKILL.md

输入:
- infer_tags.py 输出的 JSON(--json 参数)
- 调用方模型对低置信度项复核后的最终标签(JSON 文件,可选)

复核后 JSON 格式(可选输入):
[
  {
    "name": "replace-corp-trace",
    "purpose": ["替换"],
    "scope": ["2nd-components", "base-framework", "业务模块", "helm-chart"],
    "lifecycle": ["剥离中(改造)"]
  },
  ...
]

如果未提供复核 JSON,只写入高置信度项,低置信度项跳过并在 stderr 报告。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 轴在 frontmatter 中的字段名
AXIS_FIELD = {
    "purpose": "tags_purpose",
    "scope": "tags_scope",
    "lifecycle": "tags_lifecycle",
}
CATEGORY_FIELD = "category"  # 兼容字段:把 purpose 的主标签作为 category


def load_review(review_path: str | None) -> dict[str, dict]:
    """加载复核 JSON,返回 {skill_name: {axis: [tags]}}"""
    if not review_path:
        return {}
    data = json.loads(Path(review_path).read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for item in data:
        name = item.get("name")
        if not name:
            continue
        out[name] = {
            k: v
            for k, v in item.items()
            if k in ("purpose", "scope", "lifecycle") and isinstance(v, list)
        }
    return out


def pick_final_tags(inferred_item: dict, reviewed: dict[str, list] | None) -> dict[str, list[str]]:
    """为每个轴选出最终要写入的标签列表。

    优先级:
    1. 复核 JSON 中明确给出的列表(人工裁定优先)
    2. 否则取所有高置信度候选
    3. 如果都没有,返回空列表(不写入,留给下次)
    """
    reviewed = reviewed or []
    out: dict[str, list[str]] = {}
    for axis in ("purpose", "scope", "lifecycle"):
        if axis in reviewed:
            out[axis] = list(reviewed[axis])
            continue
        cands = inferred_item.get(axis, [])
        high = [c["tag"] for c in cands if c["confidence"] == "高"]
        if high:
            out[axis] = high
        else:
            out[axis] = []  # 无高置信度,不写入
    return out


def update_frontmatter(skill_md_path: Path, tags_by_axis: dict[str, list[str]]) -> tuple[bool, str]:
    """更新 SKILL.md 的 frontmatter。返回 (是否修改, 说明)。"""
    text = skill_md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False, "no frontmatter, skipped"

    end = text.find("\n---", 3)
    if end == -1:
        return False, "frontmatter 不闭合, skipped"
    fm_raw = text[3:end].strip()
    after = text[end + 4 :]

    # 检查每个轴字段是否已存在
    existing_fields = set()
    for line in fm_raw.splitlines():
        m = line.strip().split(":", 1)
        if len(m) == 2:
            existing_fields.add(m[0].strip())

    # 只补写缺失的字段
    new_lines: list[str] = []
    for axis, field in AXIS_FIELD.items():
        if field in existing_fields:
            continue
        tags = tags_by_axis.get(axis, [])
        if not tags:
            continue
        new_lines.append(f"{field}: {json.dumps(tags, ensure_ascii=False)}")

    # category 字段:取 purpose 的主标签(第一个)
    if CATEGORY_FIELD not in existing_fields:
        purpose_tags = tags_by_axis.get("purpose", [])
        if purpose_tags:
            new_lines.append(f"{CATEGORY_FIELD}: {purpose_tags[0]}")

    if not new_lines:
        return False, "all fields exist or no high-confidence tags"

    # 追加到 frontmatter 末尾
    new_fm = fm_raw.rstrip() + "\n" + "\n".join(new_lines)
    new_text = "---\n" + new_fm + "\n---" + after
    skill_md_path.write_text(new_text, encoding="utf-8")
    return True, f"wrote {len(new_lines)} field(s): {', '.join(l.split(':')[0] for l in new_lines)}"


def main():
    ap = argparse.ArgumentParser(description="把最终标签写回各 SKILL.md 的 frontmatter")
    ap.add_argument("--inferred", required=True, help="infer_tags.py 输出的 JSON(--json 参数产物)")
    ap.add_argument("--review", default="", help="调用方模型复核后的 JSON(可选)")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写文件")
    args = ap.parse_args()

    inferred = json.loads(Path(args.inferred).read_text(encoding="utf-8"))
    reviewed_map = load_review(args.review)

    root = Path(".").resolve()
    report: list[str] = []
    for item in inferred:
        name = item["name"]
        skill_md = Path(item["skill_md_path"])
        if not skill_md.is_file():
            report.append(f"[{name}] SKILL.md not found: {skill_md}")
            continue
        reviewed = reviewed_map.get(name)
        if args.review and not reviewed:
            report.append(f"[{name}] 复核 JSON 中未提供,跳过")
            continue
        final = pick_final_tags(item, reviewed)
        if args.dry_run:
            report.append(f"[{name}] (dry-run) final={final}")
            continue
        ok, msg = update_frontmatter(skill_md, final)
        report.append(f"[{name}] {'OK' if ok else 'SKIP'}: {msg}")

    sys.stderr.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
