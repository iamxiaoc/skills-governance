"""
Docker镜像构建模块
负责构建Docker镜像、推送到Harbor、触发安全扫描
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-registry"))

from corp_ci_common.logger import get_logger
from corp_ci_registry.docker_client import DockerClient
from corp_ci_registry.harbor_client import HarborClient
from corp_ci_registry.image_scanner import ImageScanner


class DockerBuilder:
    """Docker镜像构建器"""

    def __init__(self, config, logger=None, version=None):
        self.config = config
        self.logger = logger or get_logger("docker-builder")
        self.version = version or "latest"
        self.registry = config.get("docker.registry")
        self.harbor_url = config.get("docker.harbor_url")
        self.harbor_username = config.get("docker.harbor_username")
        self.harbor_password = config.get("docker.harbor_password")

        # 初始化二方件客户端
        self.docker = DockerClient(self.registry)
        self.harbor = HarborClient(self.harbor_url, self.harbor_username, self.harbor_password)
        self.scanner = ImageScanner(self.harbor)

    def build_and_push_all(self, branch, commit_id):
        """构建并推送所有微服务镜像"""
        services = self.config.get("services", [])
        self.logger.step("docker-build").info(f"开始Docker镜像构建，共 {len(services)} 个服务")

        # 登录镜像仓库
        self.logger.info("登录镜像仓库...")
        self.docker.login(self.harbor_username, self.harbor_password)

        image_tags = []
        for svc in services:
            if not svc.get("has_dockerfile", True):
                continue
            svc_name = svc["name"]
            image_name = svc["image_name"]
            module_path = svc["module"]

            try:
                tag = self._build_and_push(svc_name, image_name, module_path, branch, commit_id)
                image_tags.append(tag)

                # 安全扫描
                if self.config.get("scan.enabled", False):
                    self._scan_image(image_name, tag)

            except Exception as e:
                self.logger.fail(f"{svc_name} 镜像构建失败: {e}")
                raise

        self.logger.success(f"Docker镜像构建完成，共 {len(image_tags)} 个镜像")
        return image_tags

    def _build_and_push(self, svc_name, image_name, module_path, branch, commit_id):
        """构建并推送单个镜像"""
        full_image = self.docker.full_image_name(image_name, self.version)
        self.logger.info(f"构建镜像: {full_image}")

        # Dockerfile路径
        context_path = os.path.join(self.config.get("project.base_path"), module_path)
        dockerfile_path = os.path.join(context_path, "Dockerfile")

        # 构建镜像
        build_args = {
            "JAR_FILE": f"target/{svc_name}-{self.version}.jar",
            "SERVICE_NAME": svc_name,
        }
        self.docker.build(dockerfile_path, full_image, context_path, build_args)
        self.logger.success(f"镜像构建成功: {full_image}")

        # 推送镜像
        self.logger.info(f"推送镜像: {full_image}")
        self.docker.push(full_image)
        self.logger.success(f"镜像推送成功: {full_image}")

        # 额外打一个commitId标签
        commit_tag = self.docker.full_image_name(image_name, commit_id)
        self.docker.tag(full_image, commit_tag)
        self.docker.push(commit_tag)

        return full_image

    def _scan_image(self, image_name, full_image):
        """安全扫描镜像"""
        # 解析project和repo
        parts = image_name.split("/")
        project_name = parts[0] if len(parts) > 1 else "default"
        repo_name = parts[-1] if len(parts) > 1 else image_name

        self.logger.info(f"安全扫描镜像: {full_image}")
        max_severity = self.config.get("scan.max_severity", "High")

        passed, summary = self.scanner.scan_and_check(
            project_name, repo_name, self.version, max_severity
        )

        report = self.scanner.format_report(summary)
        self.logger.info(f"扫描结果:\n{report}")

        if not passed and self.config.get("scan.fail_on_critical", True):
            raise RuntimeError(f"镜像安全扫描未通过，存在超过 {max_severity} 级别的漏洞")

        self.logger.success(f"安全扫描通过: {full_image}")
