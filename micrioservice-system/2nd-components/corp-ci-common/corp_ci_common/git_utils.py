"""Git操作工具（二方件提供）"""

import subprocess
import os


class GitUtils:
    """Git操作封装"""

    def __init__(self, repo_path=None):
        self.repo_path = repo_path or os.getcwd()

    def _run(self, cmd):
        """执行git命令"""
        result = subprocess.run(
            cmd, cwd=self.repo_path, capture_output=True, text=True, shell=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {cmd}\nError: {result.stderr}")
        return result.stdout.strip()

    def get_current_branch(self):
        """获取当前分支"""
        return self._run("git rev-parse --abbrev-ref HEAD")

    def get_commit_id(self, short=True):
        """获取当前commit ID"""
        if short:
            return self._run("git rev-parse --short HEAD")
        return self._run("git rev-parse HEAD")

    def get_commit_message(self):
        """获取最新commit消息"""
        return self._run("git log -1 --pretty=%B")

    def get_changed_files(self, base_commit="HEAD~1"):
        """获取变更文件列表"""
        output = self._run(f"git diff --name-only {base_commit}")
        return output.split("\n") if output else []

    def get_tag(self):
        """获取最新tag"""
        try:
            return self._run("git describe --tags --abbrev=0")
        except RuntimeError:
            return None

    def checkout(self, branch):
        """切换分支"""
        return self._run(f"git checkout {branch}")

    def pull(self):
        """拉取最新代码"""
        return self._run("git pull")

    def is_dirty(self):
        """检查是否有未提交的变更"""
        output = self._run("git status --porcelain")
        return len(output) > 0
