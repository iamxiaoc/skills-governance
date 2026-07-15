"""Docker客户端（二方件提供）"""

import subprocess
import os


class DockerClient:
    """Docker操作封装"""

    def __init__(self, registry_url=None):
        self.registry_url = registry_url or os.environ.get("DOCKER_REGISTRY", "")

    def _run(self, cmd):
        """执行docker命令"""
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"Docker command failed: {cmd}\nError: {result.stderr}")
        return result.stdout.strip()

    def login(self, username, password, registry=None):
        """登录镜像仓库"""
        registry = registry or self.registry_url
        cmd = f"docker login -u {username} -p {password} {registry}"
        return self._run(cmd)

    def build(self, dockerfile_path, image_name, context_path=".", build_args=None):
        """构建Docker镜像"""
        cmd = f"docker build -f {dockerfile_path} -t {image_name} {context_path}"
        if build_args:
            for key, value in build_args.items():
                cmd += f" --build-arg {key}={value}"
        return self._run(cmd)

    def tag(self, source_image, target_image):
        """打标签"""
        return self._run(f"docker tag {source_image} {target_image}")

    def push(self, image_name):
        """推送镜像"""
        return self._run(f"docker push {image_name}")

    def pull(self, image_name):
        """拉取镜像"""
        return self._run(f"docker pull {image_name}")

    def remove_image(self, image_name):
        """删除本地镜像"""
        return self._run(f"docker rmi -f {image_name}")

    def image_exists(self, image_name):
        """检查本地镜像是否存在"""
        result = subprocess.run(
            f"docker images -q {image_name}", capture_output=True, text=True, shell=True
        )
        return len(result.stdout.strip()) > 0

    def get_image_size(self, image_name):
        """获取镜像大小"""
        output = self._run(f"docker images --format '{{{{.Size}}}}' {image_name}")
        return output

    def full_image_name(self, name, tag):
        """拼接完整镜像名"""
        if self.registry_url:
            return f"{self.registry_url}/{name}:{tag}"
        return f"{name}:{tag}"
