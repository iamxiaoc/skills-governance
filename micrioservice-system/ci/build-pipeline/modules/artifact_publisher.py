"""
构建产物发布模块
负责将Maven构建产物发布到Nexus私服
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))

from corp_ci_common.logger import get_logger
from corp_ci_common.maven_utils import MavenUtils


class ArtifactPublisher:
    """构建产物发布器"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or get_logger("artifact-publisher")
        self.project_base = config.get("project.base_path")
        self.upload_to_nexus = config.get("artifacts.upload_to_nexus", False)
        self.nexus_url = config.get("artifacts.nexus_url")
        self.maven_settings = config.get("maven.settings_path")

    def publish(self, version):
        """发布构建产物"""
        if not self.upload_to_nexus:
            self.logger.step("publish").info("跳过产物发布（未启用Nexus上传）")
            return

        services = self.config.get("services", [])
        self.logger.step("publish").info(f"发布构建产物到Nexus，共 {len(services)} 个服务")

        for svc in services:
            svc_name = svc["name"]
            module_path = svc["module"]
            try:
                self._publish_service(svc_name, module_path, version)
                self.logger.success(f"{svc_name} 产物发布成功")
            except Exception as e:
                self.logger.fail(f"{svc_name} 产物发布失败: {e}")
                raise

        self.logger.success("所有产物发布完成")

    def _publish_service(self, svc_name, module_path, version):
        """发布单个微服务产物"""
        full_path = os.path.join(self.project_base, module_path)
        maven = MavenUtils(full_path, self.maven_settings)

        # deploy到Nexus
        maven.deploy(
            profiles=self.config.get("maven.profiles"),
            mvn_opts=self.config.get("maven.jvm_opts"),
        )

        # 验证产物
        jar_path = maven.find_jar()
        if jar_path:
            self.logger.info(f"{svc_name} 产物: {jar_path}")
