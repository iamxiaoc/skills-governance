---
name: "detect-skill-overreach"
description: "检测某个 skill 执行后是否多改:对比 skill 执行前后的 git diff,检查是否有改动落在 skill 声明的'影响范围'之外。Invoke when user asks to detect overreach or check if a skill modified files outside its declared scope."
---

# Skill 越界检测(多改检测)

## 职责范围
本 skill 负责检测另一个 skill 执行后是否**多改**。它对比 skill 执行前后的 git diff,逐文件检查改动是否落在该 skill 在 SKILL.md 中声明的"影响范围"之内。任何落在声明范围之外的改动,都视为"越界"。

本 skill **不做**少改检测(那是 `verify-skill-completeness` 的职责),**不做**构建验证,不做改错的语义判断。

## 设计原则
- **跟着 skill 自声明走**:合法改动范围完全来自目标 skill 的 SKILL.md 的"影响范围"和"处理范围"小节,不维护全局路径白名单。
- **基于 git diff**:必须传入 skill 执行前的 commit SHA,通过 `git diff <before>..HEAD` 拿改动文件清单。无法回溯基线时,降级为检查未提交改动(git diff HEAD)。
- **路径匹配规则**:声明范围可能是目录(如 `base-framework/base-web/`)或文件类型(如 `所有微服务/*.java`),匹配规则按"路径前缀 + glob"解析。

## 路径匹配规则
对目标 skill 声明的每条影响范围,解析为可匹配的规则:
- 目录形式(`base-framework/base-web/`)→ 匹配该目录下所有文件
- 文件类型形式(`所有微服务/*.java` 或 `所有微服务的 pom.xml`)→ 展开为 `<每个微服务目录>/**/*.java` 或 `<每个微服务目录>/**/pom.xml`
- 单文件形式(`base-dependency/dependency-public/pom.xml`)→ 精确匹配

"所有微服务"的展开需要先扫描项目根目录下的微服务模块(如 user-module / order-module / product-module),动态识别。

## 执行步骤
1. 运行 `scripts/extract_skill_scope.py --skill <目标 skill 名>` — 从目标 SKILL.md 抽取声明的合法改动路径,解析为可匹配的 glob 规则
2. 运行 `scripts/check_overreach.py --skill <目标 skill 名> --before-sha <git commit SHA> [--project-root <根>]` — 拿 git diff,对照合法范围输出越界清单
3. 脚本输出 Markdown 报告,包含:
   - 改动文件总数
   - 合法改动文件数(落在声明范围内)
   - 越界改动文件数 + 清单(文件路径 + 改了什么)
   - 汇总结论(无越界 / 有越界)

## 约束
- 只读不写,不修改任何代码
- 不做少改检测,不做构建验证,不做接口对比
- 若未传 `--before-sha`,降级为检查未提交改动(git diff HEAD),并在报告中标注"基线:未提交改动"
- 若目标 skill 缺"影响范围"小节,所有改动都视为越界,并在报告中标注"无法确定合法范围"
- **重要**:本 skill 只检测"路径是否越界",不判断"路径内的改动内容是否正确"。内容是否正确由构建/测试判断。

## 输出示例
```
## detect-skill-overreach 报告:replace-corp-trace
- 基线: 3a2b1c0 (skill 执行前)
- 改动文件总数: 12
- 合法改动: 10 (落在声明影响范围内)
- 越界改动: 2

### 越界清单
1. ci/build-pipeline/modules/maven_builder.py
   - 改动: +3 -1 行
   - 原因: 不在声明的"影响范围"内(replace-corp-trace 只该动 base-dependency / base-framework / 微服务 / Helm Chart)
2. product-module/product-framework/pom.xml
   - 改动: +2 -0 行
   - 原因: 声明的范围是"所有微服务的 pom.xml",product-framework 属于 base-framework 层级,不算"微服务"

### 汇总结论: ❌ 有越界
- 需要人工确认 ci/build-pipeline/modules/maven_builder.py 的改动是否必要
- 需要人工确认 product-module/product-framework/pom.xml 的改动是否必要
```
