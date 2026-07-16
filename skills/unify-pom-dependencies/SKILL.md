---
name: "unify-pom-dependencies"
description: "归一化所有微服务 pom.xml 中的依赖版本声明，移除微服务自定义版本号，统一由 base-dependency 管理。Invoke when user asks to unify Maven dependency versions or fix version drift in microservice poms."
---

# POM 依赖版本归一

## 职责范围
本 skill 负责扫描所有微服务 pom.xml，移除其中直接写死的版本号，确保所有依赖版本统一由 base-dependency 管理。这是一类"多维度"skill，不针对某个具体二方件，而是处理整个依赖管理体系。

## 处理规则
1. 扫描所有微服务（user-module / order-module / product-module）及其子模块的 pom.xml
2. 对每个 `<dependency>` 节点，如果包含 `<version>` 子节点：
   - 如果该依赖在 base-dependency 的 dependencyManagement 中已声明版本 → 移除微服务 pom 中的 `<version>` 标签
   - 如果该依赖未在 base-dependency 中管理 → 报告到"未管理依赖清单"，需人工决定是否加入 base-dependency
3. 不修改 base-dependency 本身的 pom.xml
4. 不修改 base-framework 的 pom.xml（框架模块允许声明版本以便独立发布）

## 执行步骤
1. 运行 `scripts/scan_hardcoded_versions.py` — 扫描并输出所有写死版本的依赖
2. 运行 `scripts/unify_versions.py` — 移除微服务 pom 中的版本标签
3. 运行 `scripts/verify.py` — 验证移除后所有依赖仍能从 base-dependency 解析到版本

## 约束
- 只处理微服务模块的 pom.xml，不修改 base-dependency 和 base-framework
- 移除 `<version>` 前需确认 base-dependency 中已声明对应版本
- 输出"未管理依赖清单"供人工决策
