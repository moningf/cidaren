"""Token 提取 — 自动适配平台."""
import os
from typing import List


def get_all_tokens(process_name: str = "WeChatAppEx") -> List[str]:
    """从微信进程内存提取所有 Token（去重保序），失败返回空列表."""
    try:
        if os.name == "posix":
            from auth.base import find_all_tokens, get_pids
            from auth.linux import LinuxTokenScanner
            pids = get_pids(process_name)
            return find_all_tokens(LinuxTokenScanner, pids)
        elif os.name == "nt":
            from auth.base import find_all_tokens, get_pids
            from auth.windows import WindowsTokenScanner
            pids = get_pids(process_name)
            return find_all_tokens(WindowsTokenScanner, pids)
    except Exception:
        pass
    return []
