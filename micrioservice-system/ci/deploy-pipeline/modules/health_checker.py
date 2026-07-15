"""
健康检查模块
负责部署后的微服务健康检查
"""

import os
import sys
import time
import subprocess
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "2nd-components", "corp-ci-common"))

from corp_ci_common.logger import get_logger


class HealthChecker:
    """微服务健康检查器"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or get_logger("health-checker")
        self.kubeconfig = config.get("kubernetes.kubeconfig_path")
        self.context = config.get("kubernetes.context")
        self.namespace = config.get("kubernetes.namespace")
        self.check_path = config.get("health_check.check_path", "/actuator/health")
        self.timeout = config.get("health_check.timeout", 180)
        self.interval = config.get("health_check.interval", 5)
        self.helm_binary = config.get("helm.binary_path", "helm")

    def check_module(self, deployment):
        """检查整个模块的健康状态"""
        module_name = deployment["module"]
        services = deployment.get("services", [])

        self.logger.step("health-check").info(
            f"健康检查模块 {module_name}，共 {len(services)} 个服务"
        )

        for svc in services:
            svc_name = svc["name"]
            try:
                self._check_service(svc_name, deployment["release_name"])
                self.logger.success(f"{svc_name} 健康检查通过")
            except Exception as e:
                self.logger.fail(f"{svc_name} 健康检查失败: {e}")
                raise

        self.logger.success(f"模块 {module_name} 所有服务健康检查通过")

    def _check_service(self, svc_name, release_name):
        """检查单个服务的健康状态"""
        # 获取service的ClusterIP和端口
        svc_info = self._get_service_info(svc_name)
        if not svc_info:
            raise RuntimeError(f"无法获取Service信息: {svc_name}")

        cluster_ip = svc_info.get("cluster_ip")
        port = svc_info.get("port", 8080)

        if not cluster_ip:
            # 使用port-forward方式检查
            self._check_via_port_forward(svc_name, release_name)
            return

        # 直接HTTP健康检查
        url = f"http://{cluster_ip}:{port}{self.check_path}"
        self._check_http(url, svc_name)

    def _get_service_info(self, svc_name):
        """通过kubectl获取Service信息"""
        cmd = (
            f"kubectl --kubeconfig {self.kubeconfig} --context {self.context}"
            f" --namespace {self.namespace} get svc {svc_name}"
            f" -o jsonpath='{{.spec.clusterIP}},{{(index .spec.ports 0).port}}'"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0 or not result.stdout.strip():
            return None

        parts = result.stdout.strip().split(",")
        return {
            "cluster_ip": parts[0] if parts[0] != "" else None,
            "port": int(parts[1]) if len(parts) > 1 and parts[1] else 8080,
        }

    def _check_http(self, url, svc_name):
        """HTTP健康检查"""
        elapsed = 0
        while elapsed < self.timeout:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    body = resp.json()
                    status = body.get("status", "UNKNOWN")
                    if status == "UP":
                        return
                    else:
                        self.logger.warn(
                            f"{svc_name} 健康状态: {status}, 等待重试..."
                        )
            except requests.exceptions.RequestException:
                pass

            time.sleep(self.interval)
            elapsed += self.interval

        raise TimeoutError(f"{svc_name} 健康检查超时（{self.timeout}s）")

    def _check_via_port_forward(self, svc_name, release_name):
        """通过port-forward进行健康检查"""
        self.logger.info(f"使用port-forward检查 {svc_name}...")

        # 启动port-forward
        cmd = (
            f"kubectl --kubeconfig {self.kubeconfig} --context {self.context}"
            f" --namespace {self.namespace} port-forward svc/{svc_name} 18080:8080"
        )
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        try:
            time.sleep(3)  # 等待port-forward建立
            url = f"http://localhost:18080{self.check_path}"
            self._check_http(url, svc_name)
        finally:
            proc.terminate()
            proc.wait()

    def check_pod_logs(self, svc_name, tail_lines=100):
        """检查Pod日志（用于排查启动失败）"""
        cmd = (
            f"kubectl --kubeconfig {self.kubeconfig} --context {self.context}"
            f" --namespace {self.namespace} logs -l app={svc_name}"
            f" --tail={tail_lines}"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            self.logger.info(f"{svc_name} Pod日志（最后{tail_lines}行）:\n{result.stdout[-2000:]}")
        return result.stdout if result.returncode == 0 else ""
