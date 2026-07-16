---
name: "extract-component-usage"
description: "提取指定二方件在业务代码中具体使用了哪些接口/方法/字段。Invoke when user asks to extract detailed API usage of a specific 2nd-party component or to verify replacement completeness."
---

# 二方件接口/方法用法提取

## 职责范围
本 skill 仅负责提取某个指定二方件在业务代码中的具体 API 使用情况（方法、字段、构造函数等），输出"用法清单"。不执行替换。

## 触发场景
- 在替换某个二方件前，需要明确它被用到的所有方法签名
- 替换完成后，验证是否还有遗漏的二方件 API 调用
- 评估替换难度（调用的方法越多、越底层，替换难度越大）

## 支持的二方件
- `corp-trace` → 类：TraceUtils, TraceContext
- `corp-id-generator` → 类：IdGenerator, IdGeneratorFactory
- `corp-config-client` → 类：ConfigClient, ConfigChangeListener
- `corp-monitor` → 类：MonitorUtils, MonitorReporter

## 执行步骤
1. 运行 `scripts/extract_usage.py --component <二方件名>`
2. 脚本会扫描所有 .java 文件，提取：
   - import 语句
   - 类名引用（变量声明、new 实例化、静态调用）
   - 具体调用的方法名
   - 调用所在的方法/类上下文
3. 输出每个方法的使用次数和调用位置
4. 输出未被使用的方法清单（对比二方件源码，帮助判断哪些 API 可以忽略）

## 输出格式
```
=== corp-trace 用法提取 ===

[类] TraceUtils
  方法 generateTraceId()    调用 3 次
    - user-module/user-service/.../UserController.java:45
    - order-module/order-service/.../OrderService.java:78
    - product-module/product-service/.../ProductController.java:112
  方法 startTrace()         调用 1 次
    - base-framework/base-web/.../TraceFilter.java:23

[类] TraceContext
  方法 getTraceId()         调用 5 次
    ...

=== 未被使用的方法 ===
  TraceUtils.generateSpanId()  — 无调用记录
```

## 约束
- 只读不写
- 脚本需支持 `--component` 参数指定单个二方件，或 `--all` 提取全部
- 对于 Python 二方件（corp_ci_common 等），同样支持提取 import 的模块和函数
