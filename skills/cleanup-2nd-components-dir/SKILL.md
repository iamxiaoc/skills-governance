---
name: "cleanup-2nd-components-dir"
description: "清理 2nd-components 目录中已完成替换的二方件源码。Invoke when user asks to remove replaced 2nd-party component source code or clean up 2nd-components directory."
---

# 清理已完成替换的二方件源码

## 职责范围
本 skill 负责删除 `2nd-components/` 目录中已被替换的二方件源码目录。仅在确认替换完成后执行。

## 前置条件
- 对应二方件已在所有微服务、base-framework、CI 中完成替换
- 运行 `scan-2nd-components` skill 确认无残留引用
- 运行 `generate-replacement-report` skill 确认状态为"已完成"

## 执行步骤
1. 运行 `scripts/check_safe_to_delete.py --component <二方件名>` — 检查是否可安全删除
2. 如果检查通过，运行 `scripts/delete_component.py --component <二方件名>` — 删除源码目录
3. 运行 `scripts/verify_clean.py` — 验证删除后项目结构完整

## 约束
- 删除前必须检查无残留引用
- 不删除整个 2nd-components 目录，只删除已替换的单个二方件
- 删除后需更新 base-dependency/pom.xml 中可能的 modules 声明（如果有）
