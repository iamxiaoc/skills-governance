"""Harbor仓库客户端（二方件提供）"""

import requests
import json


class HarborClient:
    """Harbor镜像仓库管理客户端"""

    def __init__(self, harbor_url, username, password):
        self.harbor_url = harbor_url.rstrip("/")
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._session.auth = (username, password)

    def _request(self, method, path, **kwargs):
        """发送HTTP请求"""
        url = f"{self.harbor_url}/api/v2.0{path}"
        resp = self._session.request(method, url, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Harbor API failed: {method} {path}\n"
                f"Status: {resp.status_code}\nResponse: {resp.text}"
            )
        if resp.text:
            return resp.json()
        return None

    def create_project(self, project_name, public=False):
        """创建Harbor项目"""
        payload = {
            "project_name": project_name,
            "public": public,
            "storage_limit": -1,
        }
        return self._request("POST", "/projects", json=payload)

    def project_exists(self, project_name):
        """检查项目是否存在"""
        try:
            self._request("GET", f"/projects/{project_name}")
            return True
        except RuntimeError:
            return False

    def list_repositories(self, project_name):
        """列出项目下的所有镜像仓库"""
        return self._request("GET", f"/projects/{project_name}/repositories")

    def get_repository(self, project_name, repository_name):
        """获取镜像仓库信息"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request("GET", f"/repositories/{repo_path}")

    def list_tags(self, project_name, repository_name):
        """列出镜像的所有tag"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request(
            "GET", f"/repositories/{repo_path}/artifacts", params={"with_tag": True}
        )

    def delete_tag(self, project_name, repository_name, tag):
        """删除指定tag"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request("DELETE", f"/repositories/{repo_path}/artifacts/{tag}")

    def get_image_scan_result(self, project_name, repository_name, tag):
        """获取镜像安全扫描结果"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request(
            "GET", f"/repositories/{repo_path}/artifacts/{tag}/scan"
        )

    def trigger_scan(self, project_name, repository_name, tag):
        """触发镜像安全扫描"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request(
            "POST", f"/repositories/{repo_path}/artifacts/{tag}/scan"
        )

    def get_vulnerability_summary(self, project_name, repository_name, tag):
        """获取漏洞摘要"""
        repo_path = f"{project_name}/{repository_name}"
        return self._request(
            "GET",
            f"/repositories/{repo_path}/artifacts/{tag}/scan/result",
            params={"scan_type": "default"},
        )
