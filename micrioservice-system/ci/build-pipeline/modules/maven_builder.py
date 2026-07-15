"""
Maven构建模块
负责所有微服务的Maven编译和打包
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))

from corp_ci_common.maven_utils import MavenUtils
from corp_ci_common.logger import get_logger


class MavenBuilder:
    """Maven批量构建器"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or get_logger("maven-builder")
        self.project_base = config.get("project.base_path")
        self.maven_settings = config.get("maven.settings_path")
        self.profiles = config.get("maven.profiles")
        self.jvm_opts = config.get("maven.jvm_opts")

    def build_all(self, version):
        """构建所有微服务"""
        services = self.config.get("services", [])
        self.logger.step("maven-build").info(f"开始Maven构建，共 {len(services)} 个服务")

        # 先构建基础依赖
        self._build_base()

        # 逐个构建微服务
        success_count = 0
        failed_services = []
        for svc in services:
            svc_name = svc["name"]
            module_path = svc["module"]
            try:
                self.logger.info(f"构建 {svc_name}...")
                self._build_service(module_path, version)
                self.logger.success(f"{svc_name} 构建成功")
                success_count += 1
            except Exception as e:
                self.logger.fail(f"{svc_name} 构建失败: {e}")
                failed_services.append(svc_name)

        if failed_services:
            raise RuntimeError(f"以下服务构建失败: {', '.join(failed_services)}")

        self.logger.success(f"Maven构建完成，成功 {success_count}/{len(services)}")

    def _build_base(self):
        """构建基础依赖（base-dependency 和 base-framework）"""
        base_path = self.project_base

        # 构建 base-dependency
        dep_path = os.path.join(base_path, "base-dependency")
        self.logger.info("构建 base-dependency...")
        maven = MavenUtils(dep_path, self.maven_settings)
        maven.deploy(profiles=self.profiles, mvn_opts=self.jvm_opts)

        # 构建 base-framework
        fw_path = os.path.join(base_path, "base-framework")
        self.logger.info("构建 base-framework...")
        maven = MavenUtils(fw_path, self.maven_settings)
        maven.deploy(profiles=self.profiles, mvn_opts=self.jvm_opts)

        self.logger.success("基础依赖构建完成")

    def _build_service(self, module_path, version):
        """构建单个微服务"""
        full_path = os.path.join(self.project_base, module_path)
        maven = MavenUtils(full_path, self.maven_settings)

        # 设置版本号
        maven.set_version(version)

        # 打包（跳过测试）
        maven.package(profiles=self.profiles, mvn_opts=self.jvm_opts, skip_tests=True)

        # 查找构建产物
        jar_path = maven.find_jar()
        if not jar_path:
            raise FileNotFoundError(f"未找到构建产物jar文件: {full_path}")

        return jar_path
