---
name: "scan-2nd-components"
description: "扫描项目中所有二方件（com.corp.*）的使用情况，输出清单及引用位置。Invoke when user asks to scan/audit 2nd-party components usage or before planning component replacement."
---

# 二方件使用情况扫描

## 职责范围
本 skill 仅负责扫描和统计项目中所有二方件的使用情况，不执行任何替换或修改操作。

## 触发场景
- 需要明确项目中共使用了多少个二方件
- 需要了解每个二方件被哪些模块/微服务引用
- 在规划二方件替换工作前，需要一份完整的二方件清单作为输入

## 扫描范围
项目根目录下的以下目录均需扫描：
- `micrioservice-system/2nd-components/` — 二方件源码定义
- `micrioservice-system/base-dependency/` — 依赖版本管理
- `micrioservice-system/base-framework/` — 基础框架（可能封装了二方件）
- `micrioservice-system/user-module/` — 用户业务模块
- `micrioservice-system/order-module/` — 订单业务模块
- `micrioservice-system/product-module/` — 商品业务模块
- `micrioservice-system/ci/` — CI 流水线（Python 二方件）

## 扫描维度

### 1. Java 二方件（Maven 依赖）
通过搜索 `pom.xml` 中 groupId 为以下前缀的依赖：
- `com.corp.trace` — corp-trace 链路追踪
- `com.corp.id` — corp-id-generator 分布式ID
- `com.corp.config` — corp-config-client 配置中心客户端
- `com.corp.monitor` — corp-monitor 监控上报

对每个二方件需输出：
- 二方件坐标（groupId / artifactId / version）
- 版本定义位置（是否在 base-dependency 中统一管理）
- 被引用的模块清单（绝对路径列表）

### 2. Python 二方件（CI 流水线）
扫描 `ci/build-pipeline/` 和 `ci/deploy-pipeline/` 下的 Python 文件中的 import 语句：
- `corp_ci_common.*` — corp-ci-common
- `corp_ci_registry.*` — corp-ci-registry

### 3. 二方件源码自引用
扫描 `2nd-components/` 目录，确认二方件之间是否存在互相依赖。

## 执行步骤
1. 使用 Grep 搜索所有 `pom.xml` 中包含 `com.corp.` 的依赖声明
2. 使用 Grep 搜索所有 `.java` 文件中包含 `import com.corp.` 的语句
3. 使用 Grep 搜索 CI 目录下 `import corp_` 的 Python import
4. 汇总输出结构化清单

## 输出格式
最终以 Markdown 表格输出，包含以下列：
| 二方件名称 | groupId:artifactId | 版本 | 版本管理位置 | 引用模块数 | 引用模块清单 |

并在表格后附上"风险提示"：
- 哪些二方件版本未在 base-dependency 统一管理
- 哪些二方件被 CI 流水线直接引用（Python 侧）

## 约束
- 本 skill 只读不写，不修改任何文件
- 不进行依赖替换建议，仅输出事实清单
- 如发现二方件版本在微服务 pom 中被直接写死，需在输出中标注
