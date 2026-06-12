from typing import List

from auth.base import TokenScanner

TOKEN_PREFIX = "UserToken:"


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
            pm = pymem.Pymem(self._pid)
            addresses = pm.pattern_scan_all(
                TOKEN_PREFIX.encode("utf-8"), return_multiple=True
            )
            for addr in addresses or []:
                try:
                    data = pm.read_bytes(addr, 100).decode("utf-8")
                    token = data.replace(":", "").split()[1]
                    if token and token not in seen:
                        seen.add(token)
                        results.append(token)
                except Exception:
                    continue
        except Exception:
            pass
        return results


