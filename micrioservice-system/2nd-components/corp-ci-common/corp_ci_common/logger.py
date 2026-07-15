"""统一日志组件（二方件提供）"""

import logging
import sys
from datetime import datetime


class CiLogger:
    """CI流水线统一日志器"""

    _instances = {}

    def __init__(self, name="ci-pipeline"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self._step = ""

    def step(self, step_name):
        """设置当前步骤名"""
        self._step = step_name
        return self

    def info(self, msg):
        self.logger.info(f"[{self._step}] {msg}" if self._step else msg)

    def warn(self, msg):
        self.logger.warning(f"[{self._step}] {msg}" if self._step else msg)

    def error(self, msg):
        self.logger.error(f"[{self._step}] {msg}" if self._step else msg)

    def debug(self, msg):
        self.logger.debug(f"[{self._step}] {msg}" if self._step else msg)

    def success(self, msg):
        self.logger.info(f"✓ [{self._step}] {msg}" if self._step else f"✓ {msg}")

    def fail(self, msg):
        self.logger.error(f"✗ [{self._step}] {msg}" if self._step else f"✗ {msg}")


def get_logger(name="ci-pipeline"):
    """获取日志器实例"""
    if name not in CiLogger._instances:
        CiLogger._instances[name] = CiLogger(name)
    return CiLogger._instances[name]
