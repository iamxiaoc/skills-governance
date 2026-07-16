---
name: "replace-corp-id-generator"
description: "将 corp-id-generator 分布式ID二方件替换为部门自研 Leaf 方案。Invoke when user asks to replace corp-id-generator or migrate ID generation to Leaf."
---

# 替换 corp-id-generator 为 Leaf

## 职责范围
本 skill 专门负责将 `corp-id-generator` 二方件（com.corp.id）替换为部门自研的 Leaf ID 生成器。不处理其他二方件。

## 替换映射

| corp-id-generator 原始 API | Leaf 替代 |
|---------------------------|----------|
| `IdGenerator(workerId, datacenterId)` | `LeafSnowflakeIDGen(workerId)` |
| `IdGenerator.nextId()` | `LeafIDGen.nextId()` |
| `IdGenerator.nextBizId(prefix)` | `LeafIDGen.nextBizId(prefix)` |
| `IdGeneratorFactory.getDefault()` | `LeafIDGenFactory.getDefault()` |
| `IdGeneratorFactory.getOrCreate(w, d)` | `LeafIDGenFactory.getOrCreate(workerId)` |

## 影响范围
- `base-dependency/dependency-public/pom.xml` — 移除 corp-id-generator，添加 leaf
- `base-framework/base-middleware/` — ID 生成相关封装
- 所有微服务中使用 IdGenerator 的 Java 文件

## 执行步骤
1. 运行 `scripts/maven_replace.py` — 修改 pom.xml
2. 运行 `scripts/java_replace.py` — 替换 Java 代码

## 约束
- 仅替换 corp-id-generator
- Leaf 版本由 base-dependency 统一管理
- Leaf 需要数据库支持（用于 workerId 分配），相关配置在 ConfigMap 中管理
