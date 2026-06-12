"""Token 提取 — 自动适配平台."""
import os
from typing import List

from web.logging import app_log


def get_all_tokens(process_name: str = "") -> List[str]:
    """从微信进程内存提取所有 Token（去重保序），失败返回空列表."""
    if not process_name:
        process_name = "WeChatAppEx.exe" if os.name == "nt" else "WeChatAppEx"
    app_log("AUTH", f"平台={os.name}, 目标进程={process_name}")
    try:
        if os.name == "posix":
            from auth.base import find_all_tokens, get_pids
            from auth.linux import LinuxTokenScanner
            pids = get_pids(process_name)
            app_log("AUTH", f"Linux: 找到 {len(pids)} 个进程, PIDs={pids}")
            result = find_all_tokens(LinuxTokenScanner, pids)
            app_log("AUTH", f"Linux: 提取到 {len(result)} 个 token")
            return result
        elif os.name == "nt":
            from auth.base import find_all_tokens, get_pids
            from auth.windows import WindowsTokenScanner
            pids = get_pids(process_name)
            app_log("AUTH", f"Windows: 找到 {len(pids)} 个进程, PIDs={pids}")
            result = find_all_tokens(WindowsTokenScanner, pids)
            app_log("AUTH", f"Windows: 提取到 {len(result)} 个 token")
            return result
    except Exception as exc:
        app_log("AUTH", f"扫描异常: {exc}")
    return []
