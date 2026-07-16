#!/usr/bin/env python3
"""替换 Java 代码中 corp-monitor API 为 Micrometer"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

IMPORT_REPLACEMENTS = {
    "com.corp.monitor.MonitorUtils": "io.micrometer.core.instrument.Metrics",
    "com.corp.monitor.MonitorReporter": "io.micrometer.core.instrument.MeterRegistry",
}

CODE_REPLACEMENTS = [
    (re.compile(r"MonitorUtils\.increment\((\w+)\)"), r'Metrics.counter("\1").increment()'),
    (re.compile(r"MonitorUtils\.increment\((\w+),\s*(\w+)\)"), r'Metrics.counter("\1").increment(\2)'),
    (re.compile(r"MonitorUtils\.setGauge\((\w+),\s*(\w+)\)"), r'/* TODO: Metrics.gauge("\1", \2) */'),
    (re.compile(r"MonitorUtils\.recordTime\((\w+),\s*(\w+)\)"), r'Metrics.timer("\1").record(\2, java.util.concurrent.TimeUnit.MILLISECONDS)'),
    (re.compile(r"MonitorUtils\.startTimer\(\)"), 'Metrics.timer("method").start()'),
    (re.compile(r"MonitorUtils\.stopTimer\((\w+),\s*(\w+)\)"), r'/* TODO: \2.stop() */'),
    (re.compile(r"MonitorUtils\.getCounter\((\w+)\)"), r'Metrics.counter("\1").count()'),
]


def replace_in_java(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False
    original = content
    for old, new in IMPORT_REPLACEMENTS.items():
        content = content.replace(f"import {old};", f"import {new};")
    for pattern, replacement in CODE_REPLACEMENTS:
        content = pattern.sub(replacement, content)
    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"  已替换: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("Java 替换: corp-monitor → Micrometer")
    print("=" * 70)
    java_files = list(MICROSERVICE_DIR.rglob("*.java"))
    total = sum(1 for j in java_files if replace_in_java(j))
    print(f"\n共修改 {total} 个 Java 文件")


if __name__ == "__main__":
    main()
