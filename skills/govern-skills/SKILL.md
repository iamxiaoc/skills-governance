---
name: "govern-skills"
description: "对 skills 目录下所有 skill 进行统一的标签化与分类治理。从每个 skill 的 SKILL.md 自动推断三个分类轴的候选标签(用途/动作类型、影响范围/目录、生命周期阶段)及置信度,低置信度留给调用方模型复核,高置信度直接写入。输出双份:在每个 SKILL.md 的 frontmatter 写入 tags/category 字段,同时在 skills 根目录维护一份集中索引文件 skills-index.md。Invoke when user asks to tag/classify/govern skills or build a skills registry."
tags_purpose: ["扫描", "治理"]
tags_scope: ["skills"]
category: 扫描
---

# Skills 治理:标签化与分类

## 职责范围
本 skill 负责对 skills 目录下的所有 skill 进行统一的标签化与分类治理。它读入每个 skill 的 `SKILL.md`,从原文(职责范围、影响范围、执行步骤、触发场景等小节)中动态抽取三个分类轴的候选标签及置信度,最终输出双份结果:
1. 在每个 `SKILL.md` 的 frontmatter 中写入 `tags` 和 `category` 字段
2. 在 skills 根目录维护一份集中索引文件 `skills-index.md`

本 skill **不做**重复 skill 检测,那是另一个 skill 的职责。

## 设计原则
- **不预设轴值**:三个分类轴的取值集合完全从各 SKILL.md 原文动态抽取,脚本内部不维护任何枚举值字典。这是为了适配正式项目 80+ skills 的多样性,避免硬编码轴值导致新场景的 skill 无处归类。
- **脚本推断候选 + 模型复核**:脚本输出候选标签及置信度(高/中/低),高置信度自动写入,低置信度在索引文件中标注为 `[待复核]`,由调用方模型或人工裁定后落盘。
- **参考白皮书初步分类**:可参考 `governance/设备管理系统剥离交割白皮书.md` 中的切面划分(源码仓私有生态解耦 / 品牌特征与对外暴露清洗 / 云上资产原地无感交割 / 中间件基础设施连接管理),作为推断候选时的辅助上下文,但不作为强制枚举集合。

## 三个分类轴

### 轴 1:用途/动作类型(purpose)
描述 skill 对代码资产执行的动作类型。从 SKILL.md 的"执行步骤""职责范围"等小节抽取动词原形归并,常见取值举例(非枚举):
- `扫描` / `替换` / `修改` / `验证` / `对比` / `清理` / `归一化` / `提取` / `治理`

### 轴 2:影响范围/目录(scope)
描述 skill 实际触碰的代码目录或资产类型。从 SKILL.md 的"影响范围""处理范围""扫描范围"等小节抽取路径名,常见取值举例(非枚举):
- `2nd-components` / `base-dependency` / `base-framework` / `业务模块` / `ci` / `helm-chart` / `跨模块`

### 轴 3:生命周期阶段(lifecycle)
描述 skill 在剥离交割生命周期中的位置。参考白皮书"剥离前/剥离中/剥离后"三阶段语义,从 SKILL.md 的"触发场景""前置条件"等小节推断:
- `剥离前(评估)` / `剥离中(改造)` / `剥离后(验证)` / `收尾(清理)`

## 执行步骤
1. 运行 `scripts/scan_skills_meta.py` — 扫描 skills 目录,为每个 skill 收集元信息(SKILL.md 路径、frontmatter、正文小节标题、脚本文件清单、影响范围原文片段)
2. 运行 `scripts/infer_tags.py` — 基于上一步的元信息,推断三个轴的候选标签及置信度,输出 `skills-index.md` 草稿(含候选清单和待复核标记)
3. 调用方模型复核低置信度项,修订 `skills-index.md`
4. 运行 `scripts/write_tags_back.py` — 将最终标签写入各 SKILL.md 的 frontmatter(若已存在 tags/category 则保留人工修订值,仅在缺失时补写)

## 约束
- 不修改任何业务代码,只触碰 skills 目录下的 SKILL.md 和集中索引文件
- frontmatter 中已存在 `tags` / `category` 字段时,不覆盖人工修订值,只补写缺失字段
- 集中索引文件 `skills-index.md` 每次运行全量重写,不增量合并,避免历史污染
- 脚本对 SKILL.md 的解析必须容错:允许缺少 frontmatter、缺少某些小节、小节标题措辞不一
- 推断结果必须给出置信度,不得只输出"打上了标签"这种黑盒结论

## 输出示例
`skills-index.md` 片段:
```
## govern-skills
- purpose: 治理 [高]
- scope: skills [高]
- lifecycle: 剥离前(评估) [高]
- frontmatter 已写入: 是
- 待复核项: 无
```

低置信度示例:
```
## replace-corp-trace
- purpose: 替换 [高]
- scope: 2nd-components,base-framework,业务模块,helm-chart [高]
- lifecycle: 剥离中(改造) [中] ← 触发场景未明确阶段,凭动作推断
- frontmatter 已写入: 否(待复核后写入)
- 待复核项: lifecycle 置信度中,建议人工确认
```
