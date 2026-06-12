import re
from pathlib import Path
from typing import List, Tuple

from auth.base import TokenScanner
from web.logging import app_log

TOKEN_PREFIX = "UserToken:"


class LinuxTokenScanner(TokenScanner):
    def __init__(self, pid: int) -> None:
        self._pid = pid
        self._maps_path = Path(f"/proc/{pid}/maps")
        self._mem_path = Path(f"/proc/{pid}/mem")

    def _find_readable_segments(self) -> List[Tuple[int, int]]:
        segments: List[Tuple[int, int]] = []
        with self._maps_path.open("r") as f:
            for line in f:
                match = re.match(
                    r"([0-9a-f]+)-([0-9a-f]+)\s+([r-][w-][x-][p-])", line
                )
                if not match:
                    continue
                start = int(match.group(1), 16)
                end = int(match.group(2), 16)
                perms = match.group(3)
                if "r" in perms:
                    segments.append((start, end))
        return segments

    def _read_segment(self, start: int, end: int) -> bytes:
        with self._mem_path.open("rb") as f:
            f.seek(start)
            return f.read(end - start)

    def get_token(self) -> str:
        """取第一个匹配 token（兼容旧接口）."""
        tokens = self.get_tokens()
        return tokens[0] if tokens else ""

    def get_tokens(self) -> List[str]:
        """扫描所有可读内存段，收集全部 UserToken 出现（去重保序）."""
        results: List[str] = []
        seen: set[str] = set()
        search_bytes = TOKEN_PREFIX.encode("utf-8")
        segments = self._find_readable_segments()
        app_log("AUTH", f"Linux: PID={self._pid} 找到 {len(segments)} 个可读内存段")
        match_count = 0
        for start, end in segments:
            try:
                data = self._read_segment(start, end)
            except (PermissionError, OSError):
                continue
            pos = 0
            while True:
                index = data.find(search_bytes, pos)
                if index == -1:
                    break
                match_count += 1
                pos = index + len(search_bytes)
                content = data[index : index + 1024].decode("utf-8", errors="ignore")
                match = re.search(r"UserToken[:\s]+([a-zA-Z0-9]{10,})", content)
                if match:
                    t = match.group(1)
                    app_log("AUTH", f"Linux: PID={self._pid} 正则匹配到 token={t[:8]}...")
                    if t not in seen:
                        seen.add(t)
                        results.append(t)
                    continue
                # 兜底
                parts = content.replace(":", " ").split()
                for p in parts:
                    if len(p) > 10 and p.isalnum() and p not in seen:
                        app_log("AUTH", f"Linux: PID={self._pid} 兜底匹配到 token={p[:8]}...")
                        seen.add(p)
                        results.append(p)
        app_log("AUTH", f"Linux: PID={self._pid} 共命中 {match_count} 次, 提取 {len(results)} 个唯一 token")
        return results


