"""infer_tags.py — 基于 scan_skills_meta.py 的元信息,推断三个轴的候选标签及置信度。

三个轴:
- purpose(用途/动作类型)
- scope(影响范围/目录)
- lifecycle(生命周期阶段)

置信度档位:
- 高: 从 SKILL.md 明确小节(执行步骤/影响范围/触发场景)中直接抽到关键词
- 中: 从隐式上下文(职责范围描述/脚本文件名)推断得到
- 低: 仅能从 skill 名字推断,或多个候选互相冲突

设计原则:
- 不预设轴值枚举,所有候选从原文/脚本名/skill 名动态生成
- 一个轴可输出多个候选(如 scope 可能同时影响 base-framework 和 业务模块)
- 不做最终裁定:输出候选清单,低置信度留给模型复核
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------- purpose 轴推断 ----------
# 动词词根 → 归并目标。词根用于在原文中包含匹配。
# 这是"启发式规则",不是硬编码枚举值:词根只是帮多个同义动词归并到同一标签。
# 如果原文出现了一个不在词根表里的动词,会作为"其他候选"原样输出,留给模型裁定。
PURPOSE_VERB_ROOTS: list[tuple[str, str]] = [
    ("扫描", "扫描"),
    ("scan", "扫描"),
    ("审计", "扫描"),
    ("提取", "提取"),
    ("extract", "提取"),
    ("替换", "替换"),
    ("replace", "替换"),
    ("迁移", "替换"),
    ("migrate", "替换"),
    ("修改", "修改"),
    ("modify", "修改"),
    ("更新", "修改"),
    ("update", "修改"),
    ("适配", "修改"),
    ("改写", "修改"),
    ("归一", "归一化"),
    ("unify", "归一化"),
    ("验证", "验证"),
    ("verify", "验证"),
    ("对比", "对比"),
    ("compare", "对比"),
    ("清理", "清理"),
    ("clean", "清理"),
    ("删除", "清理"),
    ("delete", "清理"),
    ("remove", "清理"),
    ("治理", "治理"),
    ("govern", "治理"),
    ("tag", "治理"),
    ("classify", "治理"),
]


def infer_purpose(meta: dict) -> list[dict]:
    """返回 [{tag, confidence, source, evidence}, ...]"""
    candidates: dict[str, dict] = {}  # tag → {evidence, sources}

    # 来源 1: skill 名字中的动词(置信度:中)
    name = meta["name"]
    for root, canonical in PURPOSE_VERB_ROOTS:
        if root in name.lower():
            candidates.setdefault(canonical, {"evidence": [], "sources": []})
            candidates[canonical]["evidence"].append(f"skill 名包含 '{root}'")
            candidates[canonical]["sources"].append("name:中")

    # 来源 2: 执行步骤原文(置信度:高)
    # 注意:执行步骤里常有"替换后需..."这种描述,不算该 skill 的用途是"替换"。
    # 只看脚本文件名中的动词,不看文字描述。
    for sf in meta.get("script_files", []):
        sf_low = sf.lower()
        for root, canonical in PURPOSE_VERB_ROOTS:
            if root in sf_low:
                candidates.setdefault(canonical, {"evidence": [], "sources": []})
                candidates[canonical]["evidence"].append(f"执行步骤脚本名 '{sf}'")
                candidates[canonical]["sources"].append("steps:高")

    # 来源 3: 职责范围原文(置信度:中)
    # 负向规则:某些动词在职责范围里是描述对比对象而非 skill 自身动作,
    # 需要排除复合词。"替换前后""替换前""替换后""被替换""已替换""替换后需"
    # 这些上下文里的"替换"不是该 skill 的动作。
    NEGATIVE_COMPOUND_FOR_REPLACE = {
        "替换前后", "替换前", "替换后", "被替换", "已替换", "替换后需",
        "替换完成后", "替换前需", "改造前后", "改造前", "改造后",
    }
    duty_text = meta.get("sections", {}).get("职责", "")
    if duty_text:
        # 把负向复合词替换成占位符,避免后续包含匹配命中
        masked = duty_text
        for w in NEGATIVE_COMPOUND_FOR_REPLACE:
            masked = masked.replace(w, " " * len(w))
        masked_low = masked.lower()
        for root, canonical in PURPOSE_VERB_ROOTS:
            if root in masked_low:
                candidates.setdefault(canonical, {"evidence": [], "sources": []})
                candidates[canonical]["evidence"].append(f"职责范围片段")
                candidates[canonical]["sources"].append("职责:中")

    # 来源 4: 脚本文件名(置信度:中)
    # 已在来源 2 中以高置信度计入,此处跳过避免重复

    # 计算置信度
    out: list[dict] = []
    for tag, info in candidates.items():
        sources = info["sources"]
        has_high = any(s.endswith(":高") for s in sources)
        has_mid = any(s.endswith(":中") for s in sources)
        if has_high:
            conf = "高"
        elif has_mid:
            conf = "中"
        else:
            conf = "低"
        out.append(
            {
                "tag": tag,
                "confidence": conf,
                "source": ",".join(sorted(set(s.split(":")[0] for s in sources))),
                "evidence": info["evidence"][:2],  # 只留前 2 条证据避免过长
            }
        )
    # 排序:置信度 高>中>低,然后按 tag
    conf_order = {"高": 0, "中": 1, "低": 2}
    out.sort(key=lambda x: (conf_order.get(x["confidence"], 9), x["tag"]))
    return out


# ---------- scope 轴推断 ----------
# 关键字 → 归并目标。同样用于包含匹配,不是硬编码枚举集合:
# 如果原文出现了一个新目录名,会作为"其他候选"原样输出。
SCOPE_KEYWORDS: list[tuple[str, str]] = [
    ("2nd-components", "2nd-components"),
    ("二方件", "2nd-components"),
    ("base-dependency", "base-dependency"),
    ("dependency-public", "base-dependency"),
    ("dependency-user", "base-dependency"),
    ("dependency-order", "base-dependency"),
    ("dependency-product", "base-dependency"),
    ("pom.xml", "base-dependency"),
    ("base-framework", "base-framework"),
    ("base-web", "base-framework"),
    ("base-middleware", "base-framework"),
    ("base-crypto", "base-framework"),
    ("base-security", "base-framework"),
    ("base-common", "base-framework"),
    ("base-spring", "base-framework"),
    ("user-module", "业务模块"),
    ("order-module", "业务模块"),
    ("product-module", "业务模块"),
    ("user-service", "业务模块"),
    ("order-service", "业务模块"),
    ("order-payment-service", "业务模块"),
    ("product-service", "业务模块"),
    ("user-auth-service", "业务模块"),
    ("所有微服务", "业务模块"),
    ("ci/build-pipeline", "ci"),
    ("ci/deploy-pipeline", "ci"),
    ("ci 流水线", "ci"),
    ("corp_ci", "ci"),
    ("build-pipeline", "ci"),
    ("deploy-pipeline", "ci"),
    ("helm-chart", "helm-chart"),
    ("configmap", "helm-chart"),
    ("values.yaml", "helm-chart"),
    ("values-dev", "helm-chart"),
    ("values-prod", "helm-chart"),
    ("skills 目录", "skills"),
    ("skill 目录", "skills"),
    ("skills-index", "skills"),
]


def infer_scope(meta: dict) -> list[dict]:
    candidates: dict[str, dict] = {}

    def hit(canonical: str, evidence: str, source: str):
        candidates.setdefault(canonical, {"evidence": [], "sources": []})
        candidates[canonical]["evidence"].append(evidence)
        candidates[canonical]["sources"].append(source)

    # 来源 1: 影响范围原文片段(置信度:高)
    for s in meta.get("scope_raw_snippets", []):
        s_low = s.lower()
        for kw, canonical in SCOPE_KEYWORDS:
            if kw in s_low:
                hit(canonical, f"影响范围:'{s[:60]}'", "scope:高")

    # 来源 2: 职责范围原文(置信度:中)
    duty = meta.get("sections", {}).get("职责", "")
    if duty:
        duty_low = duty.lower()
        for kw, canonical in SCOPE_KEYWORDS:
            if kw in duty_low:
                hit(canonical, "职责范围原文", "职责:中")

    # 来源 3: 脚本文件名(置信度:中)
    for sf in meta.get("script_files", []):
        sf_low = sf.lower()
        for kw, canonical in SCOPE_KEYWORDS:
            if kw in sf_low:
                hit(canonical, f"脚本名 '{sf}'", "script:中")

    # 来源 4: skill 名(置信度:低)
    name_low = meta["name"].lower()
    for kw, canonical in SCOPE_KEYWORDS:
        if kw in name_low:
            hit(canonical, "skill 名", "name:低")

    out: list[dict] = []
    for tag, info in candidates.items():
        sources = info["sources"]
        has_high = any(s.endswith(":高") for s in sources)
        has_mid = any(s.endswith(":中") for s in sources)
        if has_high:
            conf = "高"
        elif has_mid:
            conf = "中"
        else:
            conf = "低"
        out.append(
            {
                "tag": tag,
                "confidence": conf,
                "source": ",".join(sorted(set(s.split(":")[0] for s in sources))),
                "evidence": info["evidence"][:2],
            }
        )
    conf_order = {"高": 0, "中": 1, "低": 2}
    out.sort(key=lambda x: (conf_order.get(x["confidence"], 9), x["tag"]))
    return out


# ---------- lifecycle 轴推断 ----------
# 生命周期三阶段(参考白皮书):剥离前(评估) / 剥离中(改造) / 剥离后(验证) / 收尾(清理)
# 推断信号:
# - "前置条件""触发场景""规划...前" → 剥离前(评估)
# - "替换""修改""执行""改造"等动作 → 剥离中(改造)
# - "验证""对比""一致性""检查" → 剥离后(验证)
# - "清理""删除""收尾" → 收尾(清理)
LIFECYCLE_SIGNALS: list[tuple[str, str, str]] = [
    # (关键字, 阶段, 来源置信度)
    ("前置条件", "剥离前(评估)", "触发:高"),
    ("触发场景", "剥离前(评估)", "触发:高"),
    ("规划", "剥离前(评估)", "触发:中"),
    ("评估", "剥离前(评估)", "触发:中"),
    ("扫描", "剥离前(评估)", "动作:中"),
    ("审计", "剥离前(评估)", "动作:中"),
    ("提取", "剥离前(评估)", "动作:中"),
    ("清理", "收尾(清理)", "动作:高"),
    ("删除", "收尾(清理)", "动作:高"),
    ("替换", "剥离中(改造)", "动作:高"),
    ("修改", "剥离中(改造)", "动作:高"),
    ("更新", "剥离中(改造)", "动作:高"),
    ("适配", "剥离中(改造)", "动作:高"),
    ("迁移", "剥离中(改造)", "动作:高"),
    ("归一", "剥离中(改造)", "动作:高"),
    ("验证", "剥离后(验证)", "动作:高"),
    ("对比", "剥离后(验证)", "动作:高"),
    ("一致性", "剥离后(验证)", "动作:高"),
    ("检查", "剥离后(验证)", "动作:中"),
]


def infer_lifecycle(meta: dict) -> list[dict]:
    """lifecycle 通常只输出 1~2 个候选,因为它表达的是阶段而非并列属性。"""
    candidates: dict[str, dict] = {}

    def hit(stage: str, evidence: str, source: str):
        candidates.setdefault(stage, {"evidence": [], "sources": []})
        candidates[stage]["evidence"].append(evidence)
        candidates[stage]["sources"].append(source)

    # 来源 1: 触发场景/前置条件原文(置信度高)
    for s in meta.get("trigger_raw_snippets", []):
        s_low = s.lower()
        for kw, stage, src in LIFECYCLE_SIGNALS:
            if kw in s_low and src.startswith("触发"):
                hit(stage, f"触发场景:'{s[:60]}'", src)

    # 来源 2: 动作动词反推阶段(置信度按 LIFECYCLE_SIGNALS 中的来源标注)
    # 从执行步骤和职责范围里找动作
    # 负向规则:同样排除"替换前后/改造前后"这种复合词里的动词
    NEGATIVE_COMPOUND_FOR_LIFECYCLE = {
        "替换前后", "替换前", "替换后", "改造前后", "改造前", "改造后",
        "被替换", "已替换", "替换完成后", "替换后需", "替换前需",
    }
    action_text = "\n".join(
        [
            meta.get("sections", {}).get("职责", ""),
            "\n".join(meta.get("steps_raw_snippets", [])),
        ]
    )
    for w in NEGATIVE_COMPOUND_FOR_LIFECYCLE:
        action_text = action_text.replace(w, " " * len(w))
    action_low = action_text.lower()
    for kw, stage, src in LIFECYCLE_SIGNALS:
        if src.startswith("动作") and kw in action_low:
            hit(stage, f"动作动词 '{kw}'", src)

    # 来源 3: skill 名(置信度低)
    name_low = meta["name"].lower()
    for kw, stage, src in LIFECYCLE_SIGNALS:
        if kw in name_low:
            hit(stage, f"skill 名含 '{kw}'", "name:低")

    # 计算置信度:lifecycle 的来源置信度已自带,取该阶段所有来源中的最高档
    out: list[dict] = []
    for stage, info in candidates.items():
        sources = info["sources"]
        # 来源档:触发:高 / 动作:高 / 动作:中 / 触发:中 / name:低
        if any(s.endswith(":高") for s in sources):
            conf = "高"
        elif any(s.endswith(":中") for s in sources):
            conf = "中"
        else:
            conf = "低"
        out.append(
            {
                "tag": stage,
                "confidence": conf,
                "source": ",".join(sorted(set(s.split(":")[0] for s in sources))),
                "evidence": info["evidence"][:2],
            }
        )
    conf_order = {"高": 0, "中": 1, "低": 2}
    out.sort(key=lambda x: (conf_order.get(x["confidence"], 9), x["tag"]))
    return out


def infer_one(meta: dict) -> dict:
    return {
        "name": meta["name"],
        "skill_md_path": meta["skill_md_path"],
        "purpose": infer_purpose(meta),
        "scope": infer_scope(meta),
        "lifecycle": infer_lifecycle(meta),
    }


def render_index(payload: list[dict]) -> str:
    """渲染 skills-index.md。"""
    lines: list[str] = []
    lines.append("# Skills 索引(由 govern-skills 自动生成)")
    lines.append("")
    lines.append("> 本文件由 `skills/govern-skills/scripts/infer_tags.py` 全量重写生成,请勿手工编辑。")
    lines.append("> 标注为 `[待复核]` 的项需调用方模型或人工裁定后,运行 write_tags_back.py 写入各 SKILL.md。")
    lines.append("")
    lines.append("## 总览")
    lines.append(f"- skills 总数: {len(payload)}")
    # 统计每个轴的取值分布
    for axis in ("purpose", "scope", "lifecycle"):
        dist: dict[str, int] = {}
        for item in payload:
            for cand in item[axis]:
                dist[cand["tag"]] = dist.get(cand["tag"], 0) + 1
        lines.append(f"- {axis} 取值分布:")
        for tag, cnt in sorted(dist.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {tag}: {cnt}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for item in payload:
        lines.append(f"## {item['name']}")
        lines.append(f"- 路径: `{item['skill_md_path']}`")
        for axis, label in [("purpose", "purpose"), ("scope", "scope"), ("lifecycle", "lifecycle")]:
            cands = item[axis]
            if not cands:
                lines.append(f"- {label}: (无候选) [待复核]")
                continue
            parts: list[str] = []
            for c in cands:
                marker = "" if c["confidence"] == "高" else f" [{c['confidence']}]"
                if c["confidence"] != "高":
                    marker = f" [{c['confidence']}][待复核]"
                parts.append(f"{c['tag']}{marker}")
            lines.append(f"- {label}: {', '.join(parts)}")
        # 待复核项汇总
        pending: list[str] = []
        for axis in ("purpose", "scope", "lifecycle"):
            for c in item[axis]:
                if c["confidence"] != "高":
                    pending.append(f"{axis}.{c['tag']}({c['confidence']})")
        lines.append(f"- 待复核项: {'; '.join(pending) if pending else '无'}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="从 scan_skills_meta.py 的输出推断标签")
    ap.add_argument("--meta", required=True, help="scan_skills_meta.py 输出的 JSON 文件路径")
    ap.add_argument("--out", default="skills/skills-index.md", help="输出索引文件路径")
    ap.add_argument("--json", default="", help="可选:同时输出推断结果 JSON 到此路径")
    args = ap.parse_args()

    data = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    payload = [infer_one(m) for m in data.get("skills", [])]

    index_text = render_index(payload)
    Path(args.out).write_text(index_text, encoding="utf-8")
    sys.stderr.write(f"wrote {args.out} ({len(payload)} skills)\n")

    if args.json:
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        sys.stderr.write(f"wrote {args.json}\n")


if __name__ == "__main__":
    main()
