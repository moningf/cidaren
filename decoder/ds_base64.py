"""DS Base64 编解码 — 对应 JS chunk-vendors 模块 86704."""
import base64
import re


def ds_decode(s: str) -> str:
    """DS.decode: URL-safe 还原 → 去除非 Base64 字符 → 标准 Base64 解码 → UTF-8."""
    s = s.replace("-", "+").replace("_", "/")
    s = re.sub(r"[^A-Za-z0-9+/]", "", s)
    padding = len(s) % 4
    if padding:
        s += "=" * (4 - padding)
    return base64.b64decode(s).decode("utf-8")


def ds_encode(text: str, url_safe: bool = False) -> str:
    """DS.encode: UTF-8 编码 → 标准 Base64."""
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    if url_safe:
        b64 = b64.replace("+", "-").replace("/", "_").rstrip("=")
    return b64
