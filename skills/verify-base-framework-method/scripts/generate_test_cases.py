#!/usr/bin/env python3
"""生成 base-framework 方法的测试用例模板"""

import json
from pathlib import Path

# 被验证的方法清单及测试用例模板
METHOD_TEMPLATES = {
    "TraceFilter.doFilter": {
        "description": "链路追踪过滤器",
        "inputs": [
            {"method": "GET", "uri": "/api/users/123", "headers": {"X-Trace-Id": ""}},
            {"method": "POST", "uri": "/api/orders", "headers": {"X-Trace-Id": "abc123"}},
        ],
        "expectedOutputs": [
            {"traceIdGenerated": True, "headerSet": "X-Trace-Id"},
            {"traceIdInherited": True, "headerSet": "X-Trace-Id"},
        ],
    },
    "IdGenService.nextId": {
        "description": "ID 生成",
        "inputs": [{}, {}, {}],
        "expectedOutputs": [
            {"format": "numeric", "length": ">10"},
            {"format": "numeric", "length": ">10"},
            {"format": "numeric", "length": ">10"},
        ],
    },
    "IdGenService.nextBizId": {
        "description": "带前缀 ID 生成",
        "inputs": [
            {"prefix": "USR"},
            {"prefix": "ORD"},
            {"prefix": "PRD"},
        ],
        "expectedOutputs": [
            {"format": "USR<number>", "startsWith": "USR"},
            {"format": "ORD<number>", "startsWith": "ORD"},
            {"format": "PRD<number>", "startsWith": "PRD"},
        ],
    },
    "ConfigService.get": {
        "description": "配置获取",
        "inputs": [
            {"key": "db.url"},
            {"key": "redis.timeout", "default": "3000"},
            {"key": "nonexistent.key"},
        ],
        "expectedOutputs": [
            {"value": "jdbc:mysql://..."},
            {"value": "3000"},
            {"value": "null"},
        ],
    },
    "MonitorService.increment": {
        "description": "监控计数",
        "inputs": [
            {"metric": "request_count"},
            {"metric": "request_count", "value": 5},
        ],
        "expectedOutputs": [
            {"counterIncremented": True},
            {"counterIncrementedBy": 5},
        ],
    },
}


def main():
    print("=" * 70)
    print("生成 base-framework 方法测试用例模板")
    print("=" * 70)

    for method, template in METHOD_TEMPLATES.items():
        print(f"\n[{method}]")
        print(f"  描述: {template['description']}")
        print(f"  测试用例数: {len(template['inputs'])}")
        for i, (inp, out) in enumerate(zip(template["inputs"], template["expectedOutputs"])):
            print(f"    用例 {i+1}: 输入={inp}  期望={out}")

    # 保存模板文件
    output = Path(__file__).parent / "test_cases_template.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(METHOD_TEMPLATES, f, ensure_ascii=False, indent=2)
    print(f"\n模板已保存: {output}")
    print("请填充实际测试数据后运行 run_comparison.py")


if __name__ == "__main__":
    main()
