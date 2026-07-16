#!/usr/bin/env python3
"""
替换 Java 代码中 corp-trace 的 API 调用为 OpenTelemetry 等价实现。
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
MICROSERVICE_DIR = PROJECT_ROOT / "micrioservice-system"

# 替换映射表：原始 import → 新 import
IMPORT_REPLACEMENTS = {
    "com.corp.trace.TraceUtils": "io.opentelemetry.api.trace.Tracer",
    "com.corp.trace.TraceContext": "io.opentelemetry.api.trace.Span",
}

# 代码片段替换规则
CODE_REPLACEMENTS = [
    # TraceUtils.generateTraceId() → 自动生成，删除该行或改为注释
    (
        re.compile(r"TraceUtils\.generateTraceId\(\)"),
        '/* TODO: traceId 由 OpenTelemetry 自动生成 */ ""',
    ),
    # TraceUtils.startTrace()
    (
        re.compile(r"TraceUtils\.startTrace\(\)"),
        'Span span = tracer.spanBuilder("method").startSpan()',
    ),
    # TraceUtils.endTrace()
    (
        re.compile(r"TraceUtils\.endTrace\(\)"),
        'span.end()',
    ),
    # TraceContext.getTraceId()
    (
        re.compile(r"TraceContext\.getTraceId\(\)"),
        'Span.current().getSpanContext().getTraceId()',
    ),
    # TraceContext.getSpanId()
    (
        re.compile(r"TraceContext\.getSpanId\(\)"),
        'Span.current().getSpanContext().getSpanId()',
    ),
    # TraceContext.clear()
    (
        re.compile(r"TraceContext\.clear\(\)"),
        '/* scope.close() 在 try-with-resources 中调用 */',
    ),
    # TraceUtils.getDuration()
    (
        re.compile(r"TraceUtils\.getDuration\(\)"),
        'span.getLatencyNanos() / 1_000_000 /* ms */',
    ),
]


def replace_in_java_file(file_path: Path):
    """替换 Java 文件中的 corp-trace API"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False

    original = content

    # 1. 替换 import 语句
    for old_import, new_import in IMPORT_REPLACEMENTS.items():
        old_pattern = f"import {old_import};"
        new_pattern = f"import {new_import};"
        content = content.replace(old_pattern, new_pattern)

    # 2. 替换代码调用
    for pattern, replacement in CODE_REPLACEMENTS:
        content = pattern.sub(replacement, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"  已替换: {file_path.relative_to(PROJECT_ROOT)}")
        return True
    return False


def main():
    print("=" * 70)
    print("Java 代码替换: corp-trace → OpenTelemetry")
    print("=" * 70)

    java_files = list(MICROSERVICE_DIR.rglob("*.java"))
    print(f"\n扫描 {len(java_files)} 个 Java 文件\n")

    total = 0
    for java in java_files:
        if replace_in_java_file(java):
            total += 1

    print(f"\n共修改 {total} 个 Java 文件")
    print("\n⚠️  后续需人工检查：")
    print("  1. Tracer 实例的注入方式（需通过 @Inject 或 Spring Bean）")
    print("  2. try-with-resources 中的 scope.close() 是否正确")
    print("  3. 跨服务调用时的 traceId 传递（需配置 W3C TraceContext 传播）")


if __name__ == "__main__":
    main()
