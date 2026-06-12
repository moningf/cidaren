"""Token 扫描器抽象基类和辅助函数."""
from abc import ABC, abstractmethod
from typing import List


class TokenScanner(ABC):
    @abstractmethod
    def get_token(self) -> str: ...

    def get_tokens(self) -> List[str]:
        """子类可覆盖：返回该进程中找到的所有 token（默认返回单条）."""
        t = self.get_token()
        return [t] if t else []


def get_pids(process_name: str) -> List[int]:
    pids: List[int] = []
    try:
        import psutil
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            if proc.info["name"] == process_name:
                pids.append(proc.info["pid"])
    except ImportError:
        pass
    return pids


def find_all_tokens(scanner_cls, pids: List[int]) -> List[str]:
    """遍历所有匹配进程，返回所有找到的 token（去重保序）."""
    seen: set[str] = set()
    result: List[str] = []
    for pid in pids:
        scanner = scanner_cls(pid)
        for token in scanner.get_tokens():
            if token and token not in seen:
                seen.add(token)
                result.append(token)
    return result
