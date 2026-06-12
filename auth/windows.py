import re
from typing import List

from auth.base import TokenScanner
from web.logging import app_log

# Windows 上 token 可能以不同形式出现在内存中
_SEARCH_PATTERNS = [
    (b"vcg_refresh_token=", re.compile(r"vcg_refresh_token=([a-zA-Z0-9]{10,})")),
    (b"UserToken:",            re.compile(r"UserToken[:\s]+([a-zA-Z0-9]{10,})")),
    (b"user_token=",           re.compile(r"user_token=([a-zA-Z0-9]{10,})")),
]


class WindowsTokenScanner(TokenScanner):
    def __init__(self, pid: int) -> None:
        self._pid = pid

    def get_token(self) -> str:
        tokens = self.get_tokens()
        return tokens[0] if tokens else ""

    def get_tokens(self) -> List[str]:
        results: List[str] = []
        seen: set[str] = set()
        try:
            import pymem
            app_log("AUTH", f"Windows: pymem 已导入, 打开 PID={self._pid}")
            pm = pymem.Pymem(self._pid)
        except ImportError:
            app_log("AUTH", "Windows: pymem 未安装")
            return []
        except Exception as exc:
            app_log("AUTH", f"Windows: 打开进程 PID={self._pid} 失败: {exc}")
            return []

        for search_bytes, regex in _SEARCH_PATTERNS:
            try:
                addresses = pm.pattern_scan_all(search_bytes, return_multiple=True)
            except Exception as exc:
                app_log("AUTH", f"Windows: pattern_scan '{search_bytes.decode()}' 失败: {exc}")
                continue

            app_log("AUTH", f"Windows: 扫描 '{search_bytes.decode()}' 找到 {len(addresses or [])} 个匹配")
            for addr in addresses or []:
                try:
                    raw = pm.read_bytes(addr, 1024)
                    data = raw.decode("utf-8", errors="ignore")
                    app_log("AUTH", f"Windows: addr={hex(addr)} data_head={data[:80]!r}")
                    match = regex.search(data)
                    if match:
                        token = match.group(1)
                        app_log("AUTH", f"Windows: '{search_bytes.decode()}' 匹配到 token={token[:8]}...")
                        if token not in seen:
                            seen.add(token)
                            results.append(token)
                        continue
                    # 兜底：按常见分隔符拆分找 token
                    parts = data.replace(":", " ").replace(";", " ").replace("=", " ").split()
                    for p in parts:
                        if len(p) > 10 and p.isalnum() and p not in seen:
                            app_log("AUTH", f"Windows: 兜底匹配到 token={p[:8]}...")
                            seen.add(p)
                            results.append(p)
                except Exception as exc:
                    app_log("AUTH", f"Windows: addr={hex(addr)} 读取失败: {exc}")
                    continue

        return results


