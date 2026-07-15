"""
Kubernetes部署模块
负责将渲染后的Helm manifest部署到K8s集群
"""

import os
import sys
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))

from corp_ci_common.logger import get_logger


class K8sDeployer:
    """K8s部署器"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or get_logger("k8s-deployer")
        self.kubeconfig = config.get("kubernetes.kubeconfig_path")
        self.context = config.get("kubernetes.context")
        self.namespace = config.get("kubernetes.namespace")
        self.timeout = config.get("kubernetes.timeout", 300)
        self.helm_binary = config.get("helm.binary_path", "helm")

    def deploy(self, module_name, deployment, rendered_manifest=None):
        """部署模块到K8s"""
        release_name = deployment["release_name"]
        chart_path = deployment["chart_path"]
        values_files = deployment.get("values_files", [])

        full_chart_path = os.path.join(
            self.config.get("helm.chart_base_path"), chart_path
        )

        self.logger.step("k8s-deploy").info(
            f"部署模块 {module_name} -> namespace={self.namespace}"
        )

        # 使用helm upgrade --install
        cmd = self._build_helm_upgrade_cmd(release_name, full_chart_path, values_files, deployment)
        self.logger.debug(f"Helm命令: {cmd}")

        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Helm部署失败: {module_name}\nCMD: {cmd}\nError: {result.stderr}"
            )

        self.logger.success(f"Helm部署成功: {module_name}")

        # 等待Pod就绪
        self._wait_for_pods(module_name, deployment)

    def _build_helm_upgrade_cmd(self, release_name, chart_path, values_files, deployment):
        """构建helm upgrade命令"""
        cmd = (
            f"{self.helm_binary} upgrade --install {release_name} {chart_path}"
            f" --kubeconfig {self.kubeconfig}"
            f" --kube-context {self.context}"
            f" --namespace {self.namespace}"
            f" --timeout {self.timeout}s"
            f" --wait"
        )
        for vf in values_files:
            vf_path = os.path.join(chart_path, vf)
            if os.path.exists(vf_path):
                cmd += f" -f {vf_path}"

        # 设置镜像版本
        image_version = deployment.get("_image_version", "latest")
        for svc in deployment.get("services", []):
            svc_name = svc["name"]
            image_name = svc["image_name"]
            registry = self.config.get("docker.registry", "registry.corp.com")
            cmd += f" --set {svc_name}.image.repository={registry}/{image_name}"
            cmd += f" --set {svc_name}.image.tag={image_version}"

        return cmd

    def _wait_for_pods(self, module_name, deployment):
        """等待Pod就绪"""
        self.logger.info(f"等待 {module_name} 的Pod就绪...")
        cmd = (
            f"kubectl --kubeconfig {self.kubeconfig} --context {self.context}"
            f" --namespace {self.namespace} wait pods"
            f" -l app.kubernetes.io/instance={deployment['release_name']}"
            f" --for=condition=Ready --timeout={self.timeout}s"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            self.logger.warn(f"部分Pod未在超时时间内就绪: {module_name}")
        else:
            self.logger.success(f"所有Pod已就绪: {module_name}")

    def rollback(self, release_name):
        """回滚Helm release"""
        self.logger.info(f"回滚 {release_name}...")
        cmd = (
            f"{self.helm_binary} rollback {release_name}"
            f" --kubeconfig {self.kubeconfig}"
            f" --kube-context {self.context}"
            f" --namespace {self.namespace}"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            self.logger.fail(f"回滚失败: {release_name}\n{result.stderr}")
        else:
            self.logger.success(f"回滚成功: {release_name}")

    def get_release_status(self, release_name):
        """获取Helm release状态"""
        cmd = (
            f"{self.helm_binary} status {release_name}"
            f" --kubeconfig {self.kubeconfig}"
            f" --kube-context {self.context}"
            f" --namespace {self.namespace}"
            f" -o json"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return None

    def list_releases(self):
        """列出所有release"""
        cmd = (
            f"{self.helm_binary} list"
            f" --kubeconfig {self.kubeconfig}"
            f" --kube-context {self.context}"
            f" --namespace {self.namespace}"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout
        return ""
