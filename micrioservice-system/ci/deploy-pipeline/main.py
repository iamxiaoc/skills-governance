#!/usr/bin/env python3
"""
发布流水线入口
负责微服务的Helm部署、配置渲染、健康检查和回滚
"""

import sys
import os

# 添加二方件到path（实际环境中通过pip install安装）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "2nd-components", "corp-ci-common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "2nd-components", "corp-ci-registry"))

from corp_ci_common.logger import get_logger
from corp_ci_common.config_loader import ConfigLoader
from corp_ci_common.git_utils import GitUtils
from corp_ci_common.notify import NotificationSender
from corp_ci_registry.harbor_client import HarborClient

from modules.helm_renderer import HelmRenderer
from modules.k8s_deployer import K8sDeployer
from modules.health_checker import HealthChecker


def main():
    logger = get_logger("deploy-pipeline")

    # Step 1: 加载配置
    logger.step("config").info("加载发布配置...")
    config = ConfigLoader(os.path.join(os.path.dirname(__file__), "config.yaml"))
    config.load()
    logger.success("配置加载完成")

    # Step 2: 获取Git信息
    logger.step("git-info").info("获取Git信息...")
    git = GitUtils(config.get("project.base_path"))
    branch = git.get_current_branch()
    commit_id = git.get_commit_id()
    logger.info(f"分支: {branch}, Commit: {commit_id}")

    # Step 3: 确定镜像版本
    image_version = f"1.0.0-{commit_id}" if branch != "main" else "1.0.0"
    logger.step("version").info(f"部署版本: {image_version}")

    # Step 4: 初始化Harbor客户端，验证镜像存在
    logger.step("verify-images").info("验证镜像存在性...")
    harbor = HarborClient(
        config.get("registry.harbor_url"),
        config.get("registry.harbor_username"),
        config.get("registry.harbor_password"),
    )
    _verify_images(harbor, config, image_version, logger)

    # Step 5: Helm渲染和部署
    deployments = config.get("deployments", [])
    logger.step("deploy").info(f"开始Helm部署，共 {len(deployments)} 个模块")

    deployed_modules = []
    for dep in deployments:
        module_name = dep["module"]
        try:
            # Helm渲染
            renderer = HelmRenderer(config, logger)
            rendered = renderer.render(dep, image_version)

            # K8s部署
            deployer = K8sDeployer(config, logger)
            deployer.deploy(module_name, dep, rendered)

            # 健康检查
            if config.get("health_check.enabled", True):
                checker = HealthChecker(config, logger)
                checker.check_module(dep)

            deployed_modules.append(module_name)
            logger.success(f"模块 {module_name} 部署成功")

        except Exception as e:
            logger.fail(f"模块 {module_name} 部署失败: {e}")

            # 回滚
            if config.get("rollback.enabled", True):
                logger.step("rollback").info(f"回滚模块 {module_name}...")
                deployer = K8sDeployer(config, logger)
                deployer.rollback(dep["release_name"])
                logger.success(f"模块 {module_name} 已回滚")

            raise

    # Step 6: 通知
    if config.get("notify.enabled", False):
        logger.step("notify").info("发送发布通知...")
        notifier = NotificationSender(
            config.get("notify.webhook_url"),
            config.get("notify.webhook_type", "dingtalk"),
        )
        title = f"发布成功 - {config.get('project.name')}"
        content = (
            f"**分支**: {branch}\n\n"
            f"**版本**: {image_version}\n\n"
            f"**Commit**: {commit_id}\n\n"
            f"**模块**: {', '.join(deployed_modules)}\n\n"
            f"**命名空间**: {config.get('kubernetes.namespace')}\n\n"
            f"**状态**: ✅ 发布成功"
        )
        notifier.notify(title, content)
        logger.success("通知发送完成")

    logger.success("发布流水线执行完成!")


def _verify_images(harbor, config, version, logger):
    """验证所有镜像在Harbor中存在"""
    deployments = config.get("deployments", [])
    for dep in deployments:
        for svc in dep.get("services", []):
            image_name = svc["image_name"]
            parts = image_name.split("/")
            project = parts[0] if len(parts) > 1 else "default"
            repo = parts[-1] if len(parts) > 1 else image_name
            try:
                harbor.get_repository(project, repo)
                logger.info(f"镜像验证通过: {image_name}:{version}")
            except Exception:
                logger.fail(f"镜像不存在: {image_name}:{version}")
                raise RuntimeError(f"镜像 {image_name}:{version} 不存在于Harbor中")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = get_logger("deploy-pipeline")
        logger.fail(f"发布流水线失败: {e}")
        sys.exit(1)
