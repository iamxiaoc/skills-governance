"""镜像安全扫描工具（二方件提供）"""

import json


class ImageScanner:
    """镜像安全扫描封装"""

    SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "None": 0}

    def __init__(self, harbor_client):
        self.harbor = harbor_client

    def scan_and_check(self, project_name, repository_name, tag, max_severity="High"):
        """扫描镜像并检查是否超过严重级别阈值"""
        # 触发扫描
        self.harbor.trigger_scan(project_name, repository_name, tag)
        # 获取扫描结果（简化版，实际应轮询等待扫描完成）
        import time
        time.sleep(5)
        result = self.harbor.get_vulnerability_summary(
            project_name, repository_name, tag
        )
        summary = self._parse_summary(result)
        passed = self._check_severity(summary, max_severity)
        return passed, summary

    def _parse_summary(self, scan_result):
        """解析扫描结果摘要"""
        summary = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "total": 0,
        }
        if not scan_result:
            return summary
        vulnerabilities = scan_result.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "Unknown")
            if severity in summary:
                summary[severity] += 1
            summary["total"] += 1
        return summary

    def _check_severity(self, summary, max_severity):
        """检查是否超过严重级别阈值"""
        max_level = self.SEVERITY_ORDER.get(max_severity, 3)
        for severity, count in summary.items():
            if severity == "total":
                continue
            if count > 0 and self.SEVERITY_ORDER.get(severity, 0) > max_level:
                return False
        return True

    def format_report(self, summary):
        """格式化扫描报告"""
        lines = [
            f"镜像安全扫描报告",
            f"  Critical: {summary['Critical']}",
            f"  High:     {summary['High']}",
            f"  Medium:   {summary['Medium']}",
            f"  Low:      {summary['Low']}",
            f"  Total:    {summary['total']}",
        ]
        return "\n".join(lines)
