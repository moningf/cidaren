"""HTTP 请求封装 — Session 管理 + 响应解码."""
from typing import Any, Callable, Dict, Optional

import requests

from decoder.response_decoder import ResponseDecoder


class TokenExpiredError(Exception):
    """Token 已过期或失效."""
    pass


class BaseAPI:
    def __init__(self, decoder: ResponseDecoder) -> None:
        self._session = requests.Session()
        self._decoder = decoder
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36 "
                "MicroMessenger/7.0.20.1781(0x6700143B) "
                "WindowsWechat(0x63090a13)"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        self.on_token_expired: Optional[Callable[[], None]] = None

    def set_token(self, token: str) -> None:
        self._session.headers["UserToken"] = token

    def _check_response(self, resp: Dict[str, Any]) -> Dict[str, Any]:
        """检查响应是否表示 token 过期."""
        code = resp.get("code")
        msg = str(resp.get("msg", "")).lower()
        # code 不为 1 且消息包含 token/登录/授权相关关键词
        if code != 1 and any(k in msg for k in ("token", "登录", "授权", "auth", "expire", "过期", "无效")):
            if self.on_token_expired:
                self.on_token_expired()
            raise TokenExpiredError(f"Token 已过期: {resp.get('msg', '未知错误')}")
        return resp

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        resp = self._session.post(url, json=data, timeout=30, **kwargs)
        if resp.status_code == 401:
            if self.on_token_expired:
                self.on_token_expired()
            raise TokenExpiredError("HTTP 401: Token 已过期")
        resp.raise_for_status()
        decoded = self._decoder.decode(resp.text)
        return self._check_response(decoded)

    def get(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        resp = self._session.get(url, timeout=30, **kwargs)
        if resp.status_code == 401:
            if self.on_token_expired:
                self.on_token_expired()
            raise TokenExpiredError("HTTP 401: Token 已过期")
        resp.raise_for_status()
        decoded = self._decoder.decode(resp.text)
        return self._check_response(decoded)
