"""Maven构建工具（二方件提供）"""

import subprocess
import os


class MavenUtils:
    """Maven构建封装"""

    def __init__(self, project_path=None, settings_path=None):
        self.project_path = project_path or os.getcwd()
        self.settings_path = settings_path or os.environ.get(
            "MAVEN_SETTINGS", "/opt/maven/settings.xml"
        )

    def _build_cmd(self, goals, profiles=None, mvn_opts=None):
        """构建mvn命令"""
        cmd = f"mvn -s {self.settings_path} -f {self.project_path}/pom.xml"
        if profiles:
            cmd += f" -P {profiles}"
        if mvn_opts:
            cmd += f" {mvn_opts}"
        cmd += f" {goals}"
        return cmd

    def _run(self, cmd):
        """执行命令"""
        result = subprocess.run(
            cmd, cwd=self.project_path, capture_output=True, text=True, shell=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Maven build failed:\nCMD: {cmd}\nSTDERR: {result.stderr[-2000:]}"
            )
        return result.stdout

    def clean_compile(self, profiles=None, mvn_opts=None):
        """清理编译"""
        cmd = self._build_cmd("clean compile", profiles, mvn_opts)
        return self._run(cmd)

    def package(self, profiles=None, mvn_opts=None, skip_tests=False):
        """打包"""
        goals = "clean package"
        if skip_tests:
            goals += " -DskipTests"
        cmd = self._build_cmd(goals, profiles, mvn_opts)
        return self._run(cmd)

    def deploy(self, profiles=None, mvn_opts=None):
        """部署到私服"""
        cmd = self._build_cmd("clean deploy -DskipTests", profiles, mvn_opts)
        return self._run(cmd)

    def get_version(self):
        """获取项目版本号"""
        cmd = self._build_cmd("help:evaluate -Dexpression=project.version -q -DforceStdout")
        output = self._run(cmd)
        return output.strip()

    def set_version(self, new_version):
        """设置项目版本号"""
        cmd = self._build_cmd(f"versions:set -DnewVersion={new_version} -DgenerateBackupPoms=false")
        return self._run(cmd)

    def find_jar(self, module_name=None):
        """查找构建产物jar文件"""
        target_dir = os.path.join(self.project_path, module_name, "target") if module_name else os.path.join(self.project_path, "target")
        if not os.path.exists(target_dir):
            return None
        for f in os.listdir(target_dir):
            if f.endswith(".jar") and "sources" not in f and "javadoc" not in f:
                return os.path.join(target_dir, f)
        return None
