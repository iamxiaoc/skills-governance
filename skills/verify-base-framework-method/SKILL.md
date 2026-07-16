---
name: "verify-base-framework-method"
description: "对比 base-framework 中封装二方件的方法在替换前后行为是否一致。Invoke when user asks to verify framework method behavior consistency after component replacement."
---

# 验证 base-framework 方法一致性

## 职责范围
本 skill 负责对比 `base-framework` 中封装了二方件的方法，在替换前后行为是否一致。通过输入输出对比来验证封装层是否正确适配了新组件。只读不写。

## 验证方法
对于 base-framework 中的每个封装方法：
1. 准备一组测试输入数据
2. 在改造前的代码上运行，记录输出
3. 在改造后的代码上运行，记录输出
4. 对比两次输出是否一致

## 被验证的方法清单
- `base-web/TraceFilter.doFilter()` — 链路追踪过滤器
- `base-middleware/IdGenService.nextId()` — ID 生成
- `base-middleware/IdGenService.nextBizId(prefix)` — 带前缀 ID 生成
- `base-middleware/ConfigService.get(key)` — 配置获取
- `base-middleware/MonitorService.increment(name)` — 监控计数
- `base-crypto/CryptoService.encrypt(data)` — 加密（依赖配置中心获取密钥）

## 执行步骤
1. 运行 `scripts/generate_test_cases.py` — 生成测试用例模板
2. 用户填充测试数据
3. 运行 `scripts/run_comparison.py --method <方法名> --input <输入.json>`
4. 脚本输出对比结果

## 约束
- 只对比方法的输入输出，不验证内部实现
- 对于有副作用的方法（如监控上报），需 mock 外部依赖
- ID 生成类方法因 ID 唯一性，需对比格式而非具体值
