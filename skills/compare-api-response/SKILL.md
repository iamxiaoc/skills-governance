---
name: "compare-api-response"
description: "对比前后改造同一微服务的接口响应体是否一致（剔除时间戳、traceId 等干扰字段）。Invoke when user asks to verify API response consistency before and after refactoring."
---

# 对比接口响应体一致性

## 职责范围
本 skill 负责对比某个微服务在改造前后，同一接口的响应体是否一致。用于验证二方件替换后接口行为未发生破坏性变化。只读不写，不修改任何代码。

## 对比策略
1. **剔除动态字段**：以下字段的值在每次请求中会变化，对比时需忽略其值
   - `timestamp` / `ts` / `time`
   - `traceId` / `spanId` / `requestId`
   - `id`（自增ID或雪花ID）
   - `createdAt` / `updatedAt`
   - `token` / `accessToken` / `refreshToken`
   - `signature` / `sign`
2. **结构对比**：对比 JSON 的 key 结构是否一致（字段名、嵌套层级）
3. **类型对比**：对比字段的数据类型是否一致（int → long 视为变更）
4. **值对比**：对静态字段对比值是否一致

## 执行步骤
1. 运行 `scripts/diff_response.py --before <改造前响应.json> --after <改造后响应.json>`
2. 脚本会输出：
   - 结构差异（新增/缺失的字段）
   - 类型差异
   - 值差异（已剔除动态字段）
3. 如果差异为空，则接口响应一致

## 输出格式
```
=== 接口对比: /api/users/123 ===

[结构差异]
  ❌ 改造后缺失字段: data.createdAt
  ❌ 改造后新增字段: data.createTime

[类型差异]
  ⚠️  data.userId: Long → String

[值差异]（已剔除动态字段）
  ✅ 无值差异

结论: ❌ 存在差异，需人工确认
```

## 约束
- 只对比 JSON 响应体，不对比 HTTP 头
- 动态字段清单可通过 `--ignore-fields` 参数扩展
- 不发起真实 HTTP 请求，需用户预先保存响应文件
