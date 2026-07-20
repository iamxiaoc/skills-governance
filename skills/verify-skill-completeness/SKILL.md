---
name: "verify-skill-completeness"
description: "检测某个 skill 执行后是否少改:对照该 skill 在 SKILL.md 中声明的'影响范围'与'约束',逐项检查目标目录/文件是否还有残留指纹。Invoke when user asks to verify a skill's completeness or check for missed changes after a skill run."
---

# Skill 完整性检测(少改检测)

## 职责范围
本 skill 负责检测另一个 skill 执行后是否**少改**。它对照目标 skill 在 SKILL.md 中声明的"影响范围"和"约束"小节,逐项检查这些路径下是否还有应该被清理但残留的指纹(import、依赖声明、配置项、类名引用等)。

本 skill **不做**多改检测(那是 `detect-skill-overreach` 的职责),**不做**构建验证(那是 `verify-build-passes` 的职责),**不做**改错的语义判断。

## 设计原则
- **跟着 skill 自声明走**:检查点完全来自目标 skill 的 SKILL.md 的"影响范围"和"约束"小节,不维护全局指纹映射表。这样不管正式项目有 80 个还是 800 个 skill,每个 skill 自治声明自己该清理什么。
- **静态匹配残留指纹**:检查方式为对声明的路径做 Grep 静态扫描,不依赖运行时,置信度高。
- **容错**:目标 skill 若缺失"影响范围"小节,在报告中标注"无法检测:缺影响范围声明",不报错。

## 检查点抽取
从目标 SKILL.md 的"影响范围""处理范围""扫描范围"等小节抽取以下信息:
1. **目录路径**(如 `base-framework/base-web/`、`所有微服务`)
2. **文件类型**(如 `.java`、`pom.xml`、`ConfigMap`)
3. **预期清理的指纹**(从 skill 的"替换映射""处理规则"等小节抽取旧 token,如 `com.corp.trace`、`corp-trace-server`)

## 残留指纹类型
对每个声明的路径,扫描以下残留信号:
- **import 残留**:Java 的 `import com.corp.*`、Python 的 `from corp_* import`
- **依赖残留**:pom.xml 中仍有 `<groupId>com.corp</groupId>`、requirements.txt 中仍有 `corp-*`
- **配置残留**:ConfigMap/values.yaml 中仍有旧配置项(如 `corp-trace-server`)
- **类名/方法引用残留**:.java 文件中仍出现旧类名(如 `TraceUtils`、`ConfigClient`)

## 执行步骤
1. 运行 `scripts/extract_skill_targets.py --skill <目标 skill 名>` — 从目标 SKILL.md 抽取声明的检查点(路径 + 文件类型 + 指纹清单)
2. 运行 `scripts/check_residuals.py --skill <目标 skill 名> --project-root <项目根>` — 对每个检查点执行 Grep 扫描,输出残留清单
3. 脚本输出 Markdown 报告,包含:
   - 每个检查点的扫描结果(✅ 无残留 / ❌ 有残留 + 位置清单)
   - 汇总结论(完整 / 有遗漏)
   - 声明缺失提示(若目标 skill 缺影响范围小节)

## 约束
- 只读不写,不修改任何代码
- 不做构建验证,不做接口对比,不做多改检测
- 检查点必须来自目标 skill 的 SKILL.md 声明,不靠本 skill 内置规则推断"应该检查什么"
- 若目标 skill 的"影响范围"小节缺失或措辞模糊,在报告中明确标注"无法自动检测",不强行猜测

## 输出示例
```
## verify-skill-completeness 报告:replace-corp-trace

### 声明检查点(来自 SKILL.md 影响范围)
1. base-dependency/dependency-public/pom.xml — 指纹: com.corp.trace
2. base-framework/base-web/ — 指纹: com.corp.trace, TraceUtils, TraceContext
3. base-framework/base-middleware/ — 指纹: com.corp.trace
4. 所有微服务/*/pom.xml — 指纹: com.corp.trace
5. 所有微服务/**/*.java — 指纹: TraceUtils, TraceContext

### 扫描结果
1. ✅ base-dependency/dependency-public/pom.xml — 无残留
2. ❌ base-framework/base-web/src/main/java/com/corp/web/TraceFilter.java:23
   - 残留: `import com.corp.trace.TraceContext;`
3. ✅ base-framework/base-middleware/ — 无残留
4. ❌ user-module/user-service/pom.xml:45
   - 残留: `<artifactId>corp-trace</artifactId>`
5. ✅ 所有微服务 *.java — 无残留

### 汇总结论: ❌ 有遗漏
- 残留检查点数: 2 / 5
- 需要回看 replace-corp-trace 的执行,补改遗漏的 2 处
```
