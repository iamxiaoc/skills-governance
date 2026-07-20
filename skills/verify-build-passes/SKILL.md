---
name: "verify-build-passes"
description: "在 skill 执行后运行构建命令(mvn compile / py_compile),验证语法和依赖是否正确,不看测试结果。Invoke when user asks to verify build passes after a skill run or check if code compiles."
---

# 构建验证(语法与依赖)

## 职责范围
本 skill 负责在另一个 skill 执行后,运行构建命令验证代码是否仍能编译。它只看**语法和依赖**是否正确,**不跑测试**。这是改错检测的最底层:如果连编译都过不了,说明 skill 改的代码有语法错误或依赖缺失,根本不用谈"改对没改对"。

本 skill **不做**少改检测、多改检测、接口对比、方法行为对比。它的定位是改错检测的第一道闸门:构建不通过 = 改错了(至少语法错)。

## 设计原则
- **只 compile 不 test**:理由是 skill 改完代码只能保证语法和依赖正确。单测是否过属于业务测试范畴,skill 不背这个锅。跑 test 会拉长验证时间且大量失败可能与 skill 无关。
- **按项目类型分发**:根据传入的项目根目录下的文件类型自动选择构建工具(Maven 项目走 mvn,Python 项目走 py_compile),不要求用户手动指定。
- **看 exit code**:只关心构建命令的 exit code,0 = 通过,非 0 = 失败。失败时输出错误摘要(前 N 行 stderr)。

## 构建命令选择
根据项目根目录的文件类型自动判断:
- **Maven 项目**(根目录或子目录有 `pom.xml`):执行 `mvn -q compile -DskipTests`,如有 `-pl` 子模块参数可选传入
- **Python 项目**(根目录或子目录有 `*.py` 但无 pom.xml):对每个 `.py` 文件执行 `python -m py_compile`,逐个检查
- **混合项目**:同时执行两种验证,任何一种失败都报失败

## 执行步骤
1. 运行 `scripts/detect_project_type.py --project-root <项目根>` — 探测项目类型(Maven / Python / 混合)
2. 运行 `scripts/run_build.py --project-root <项目根> [--mvn-args "..."] [--py-files "..."]` — 执行构建命令,捕获 exit code 和 stderr
3. 脚本输出 Markdown 报告,包含:
   - 项目类型
   - 构建命令(可复现)
   - exit code
   - 失败时的错误摘要(前 50 行 stderr)
   - 汇总结论(通过 / 失败)

## 约束
- 只读项目(不修改源码),允许 `mvn` 写 target/ 等构建产物
- **不跑测试**:任何 `-Dtest=` / `-Dgroups=` 参数将被忽略并提示
- **不解析错误**:只输出错误摘要,不尝试定位是哪个 skill 改错了——那是人工或后续 skill 的事
- 不依赖 skill 的声明信息,纯靠构建工具的客观结果判断
- 若 mvn/pytest 等命令本身不存在,报"工具缺失"而不是"构建失败"

## 输出示例
```
## verify-build-passes 报告
- 项目类型: Maven
- 构建命令: mvn -q compile -DskipTests
- exit code: 1
- 结论: ❌ 失败

### 错误摘要(前 50 行 stderr)
[ERROR] base-framework/base-web/src/main/java/com/corp/web/TraceFilter.java:[23,17] 错误: 找不到符号
[ERROR]   符号:   变量 TraceContext
[ERROR]   位置: 类 TraceFilter
...
```

通过示例:
```
## verify-build-passes 报告
- 项目类型: Maven
- 构建命令: mvn -q compile -DskipTests
- exit code: 0
- 结论: ✅ 通过
```
