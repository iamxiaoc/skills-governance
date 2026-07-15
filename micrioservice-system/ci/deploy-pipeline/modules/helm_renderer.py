"""
Helm渲染模块
负责Helm Chart的values渲染和模板生成
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))

from corp_ci_common.logger import get_logger


class HelmRenderer:
    """Helm Chart渲染器"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or get_logger("helm-renderer")
        self.helm_binary = config.get("helm.binary_path", "helm")
        self.chart_base_path = config.get("helm.chart_base_path")

    def render(self, deployment, image_version):
        """渲染Helm Chart"""
        module_name = deployment["module"]
        chart_path = deployment["chart_path"]
        release_name = deployment["release_name"]
        values_files = deployment.get("values_files", [])

        full_chart_path = os.path.join(self.chart_base_path, chart_path)
        self.logger.info(f"渲染Helm Chart: {module_name} (chart: {chart_path})")

        # 构建helm template命令
        cmd = f"{self.helm_binary} template {release_name} {full_chart_path}"
        for vf in values_files:
            vf_path = os.path.join(full_chart_path, vf)
            if os.path.exists(vf_path):
                cmd += f" -f {vf_path}"
            else:
                self.logger.warn(f"values文件不存在，跳过: {vf_path}")

        # 添加镜像版本参数
        for svc in deployment.get("services", []):
            svc_name = svc["name"]
            image_name = svc["image_name"]
            registry = self.config.get("docker.registry", "registry.corp.com")
            full_image = f"{registry}/{image_name}:{image_version}"
            cmd += f" --set {svc_name}.image.repository={registry}/{image_name}"
            cmd += f" --set {svc_name}.image.tag={image_version}"

        self.logger.debug(f"Helm命令: {cmd}")

        # 执行helm template
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Helm渲染失败: {module_name}\nCMD: {cmd}\nError: {result.stderr}"
            )

        rendered = result.stdout
        self.logger.success(f"Helm渲染成功: {module_name}")
        return rendered

    def lint(self, chart_path):
        """Helm Chart语法检查"""
        full_path = os.path.join(self.chart_base_path, chart_path)
        cmd = f"{self.helm_binary} lint {full_path}"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            self.logger.fail(f"Helm lint失败: {chart_path}\n{result.stderr}")
            return False
        self.logger.success(f"Helm lint通过: {chart_path}")
        return True
