#!/usr/bin/env python3
"""修改 base-web：TraceFilter 适配 OpenTelemetry"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BASE_WEB_DIR = PROJECT_ROOT / "micrioservice-system" / "base-framework" / "base-web"

IMPORT_REPLACEMENTS = {
    "com.corp.trace.TraceUtils": "io.opentelemetry.api.trace.Tracer",
    "com.corp.trace.TraceContext": "io.opentelemetry.api.trace.Span",
    "com.corp.config.ConfigClient": "org.springframework.beans.factory.annotation.Value",
}

CODE_REPLACEMENTS = [
    (re.compile(r"TraceUtils\.startTrace\(\)"), 'span = tracer.spanBuilder("request").startSpan()'),
    (re.compile(r"TraceUtils\.endTrace\(\)"), 'span.end()'),
    (re.compile(r"TraceContext\.getTraceId\(\)"), 'Span.current().getSpanContext().getTraceId()'),
    (re.compile(r"configClient\.getConfig\(\"(\w+)\"\)"), r'/* @Value("${\1}") */ null'),
]


def update_java(file_path: Path):
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
        print(f"  已更新: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("更新 base-web")
    print("=" * 70)
    if not BASE_WEB_DIR.exists():
        print("base-web 目录不存在")
        return
    total = sum(1 for j in BASE_WEB_DIR.rglob("*.java") if update_java(j))
    print(f"\n共修改 {total} 个 Java 文件")


if __name__ == "__main__":
    main()
