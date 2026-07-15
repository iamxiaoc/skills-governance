"""配置加载组件（二方件提供）"""

import os
import yaml


class ConfigLoader:
    """CI流水线配置加载器，支持多环境配置合并"""

    def __init__(self, config_path=None):
        self.config_path = config_path or os.environ.get("CI_CONFIG_PATH", "config.yaml")
        self._config = {}

    def load(self):
        """加载主配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}
        # 加载环境覆盖配置
        env = os.environ.get("CI_ENV", "dev")
        env_config_path = self.config_path.replace(".yaml", f"-{env}.yaml")
        if os.path.exists(env_config_path):
            with open(env_config_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
            self._merge(self._config, env_config)
        return self

    def _merge(self, base, override):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def get(self, key_path, default=None):
        """通过点号路径获取配置值，如 get('build.jvm_opts')"""
        keys = key_path.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_section(self, section_name):
        """获取整个配置段"""
        return self._config.get(section_name, {})

    def get_all(self):
        """获取全部配置"""
        return self._config
