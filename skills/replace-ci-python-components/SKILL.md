---
name: "replace-ci-python-components"
description: "替换 CI 流水线中 corp-ci-common 和 corp-ci-registry 两个 Python 二方件为开源方案。Invoke when user asks to replace CI Python 2nd-party components or migrate CI tooling."
---

# 替换 CI Python 二方件

## 职责范围
本 skill 负责替换 CI 流水线（Python 代码）中的两个二方件：
- `corp-ci-common` → 替换为标准开源库（logging、pyyaml、gitpython、jinja2）
- `corp-ci-registry` → 替换为 docker-py 和 harborapi

## 替换映射

### corp-ci-common
| 原始模块 | 开源替代 | 说明 |
|---------|---------|------|
| `corp_ci_common.logger` | `logging` + `loguru` | 日志 |
| `corp_ci_common.config_loader` | `yaml` (pyyaml) | 配置加载 |
| `corp_ci_common.git_utils` | `git` (gitpython) | Git 操作 |
| `corp_ci_common.maven_utils` | `subprocess` | Maven 命令执行 |
| `corp_ci_common.notify` | `requests` | 通知发送（钉钉/企业微信 webhook） |

### corp-ci-registry
| 原始模块 | 开源替代 | 说明 |
|---------|---------|------|
| `corp_ci_registry.docker_client` | `docker` (docker-py) | Docker 客户端 |
| `corp_ci_registry.harbor_client` | `requests` | Harbor API 调用 |
| `corp_ci_registry.image_scanner` | `trufflepy` 或 `subprocess` 调用 trivy | 镜像扫描 |

## 影响范围
- `ci/build-pipeline/main.py` — 构建流水线入口
- `ci/build-pipeline/modules/*.py` — 构建模块
- `ci/deploy-pipeline/main.py` — 部署流水线入口
- `ci/deploy-pipeline/modules/*.py` — 部署模块
- `ci/build-pipeline/requirements.txt` — 依赖声明
- `ci/deploy-pipeline/requirements.txt` — 依赖声明

## 执行步骤
1. 运行 `scripts/scan_python_imports.py` — 扫描所有二方件 import
2. 运行 `scripts/replace_imports.py` — 替换 import 语句
3. 运行 `scripts/update_requirements.py` — 更新 requirements.txt
4. 运行 `scripts/rewrite_code.py` — 改写代码逻辑（API 调用方式不同需适配）

## 约束
- 仅处理 ci/ 目录下的 Python 代码
- 不修改 micrioservice-system/ 下其他目录
- 替换后需确保 CI 流水线能在无 corp 二方件的环境运行
