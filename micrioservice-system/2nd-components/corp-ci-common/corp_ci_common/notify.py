"""通知组件（二方件提供）"""

import json
import requests


class NotificationSender:
    """CI流水线通知发送器，支持钉钉/飞书/企业微信"""

    def __init__(self, webhook_url=None, webhook_type="dingtalk"):
        self.webhook_url = webhook_url
        self.webhook_type = webhook_type

    def send_dingtalk(self, title, content, is_at_all=False):
        """发送钉钉通知"""
        if not self.webhook_url:
            return
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
            "at": {"isAtAll": is_at_all},
        }
        resp = requests.post(self.webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"DingTalk notify failed: {resp.text}")

    def send_feishu(self, title, content):
        """发送飞书通知"""
        if not self.webhook_url:
            return
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
        resp = requests.post(self.webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Feishu notify failed: {resp.text}")

    def notify(self, title, content):
        """统一通知入口"""
        if self.webhook_type == "dingtalk":
            self.send_dingtalk(title, content)
        elif self.webhook_type == "feishu":
            self.send_feishu(title, content)
