#!/usr/bin/env python3
"""
构建流水线入口
负责微服务的Maven编译、Docker镜像构建、推送和安全扫描
"""

import sys
import os

# 添加二方件到path（实际环境中通过pip install安装）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "2nd-components", "corp-ci-common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "2nd-components", "corp-ci-registry"))

from corp_ci_common.logger import get_logger
from corp_ci_common.config_loader import ConfigLoader
from corp_ci_common.git_utils import GitUtils
from corp_ci_common.maven_utils import MavenUtils
from corp_ci_common.notify import NotificationSender
from corp_ci_registry.docker_client import DockerClient
from corp_ci_registry.harbor_client import HarborClient
from corp_ci_registry.image_scanner import ImageScanner

from modules.maven_builder import MavenBuilder
from modules.docker_builder import DockerBuilder
from modules.artifact_publisher import ArtifactPublisher


def main():
    logger = get_logger("build-pipeline")

    # Step 1: 加载配置
    logger.step("config").info("加载构建配置...")
    config = ConfigLoader(os.path.join(os.path.dirname(__file__), "config.yaml"))
    config.load()
    logger.success("配置加载完成")

    # Step 2: 获取Git信息
    logger.step("git-info").info("获取Git信息...")
    git = GitUtils(config.get("project.base_path"))
    branch = git.get_current_branch()
    commit_id = git.get_commit_id()
    commit_msg = git.get_commit_message()
    logger.info(f"分支: {branch}, Commit: {commit_id}")
    logger.info(f"Commit消息: {commit_msg}")

    # Step 3: 确定版本号
    version = f"1.0.0-{commit_id}" if branch != "main" else "1.0.0"
    logger.step("version").info(f"构建版本: {version}")

    # Step 4: Maven构建
    maven_builder = MavenBuilder(config, logger)
    maven_builder.build_all(version)

    # Step 5: 构建产物发布
    publisher = ArtifactPublisher(config, logger)
    publisher.publish(version)

    # Step 6: Docker镜像构建和推送
    docker_builder = DockerBuilder(config, logger, version)
    docker_builder.build_and_push_all(branch, commit_id)

    # Step 7: 通知
    if config.get("notify.enabled", False):
        logger.step("notify").info("发送构建通知...")
        notifier = NotificationSender(
            config.get("notify.webhook_url"),
            config.get("notify.webhook_type", "dingtalk"),
        )
        title = f"构建成功 - {config.get('project.name')}"
        content = (
            f"**分支**: {branch}\n\n"
            f"**版本**: {version}\n\n"
            f"**Commit**: {commit_id}\n\n"
            f"**服务数**: {len(config.get('services', []))}\n\n"
            f"**状态**: ✅ 构建成功"
        )
        notifier.notify(title, content)
        logger.success("通知发送完成")

    logger.success("构建流水线执行完成!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = get_logger("build-pipeline")
        logger.fail(f"构建流水线失败: {e}")
        sys.exit(1)
