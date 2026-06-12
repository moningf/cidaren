"""统一日志系统 — 所有日志写入 logs/cidaren_YYYYMMDD.log."""
import traceback as tb
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

_LOG_DIR = Path(__file__).parent.parent / "logs"
_MAX_MEM_LOGS = 500
_KEEP_DAYS = 7
_TAG_WIDTH = 4


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _cleanup_dir() -> None:
    """清理超过 _KEEP_DAYS 天的日志文件."""
    cutoff = datetime.now() - timedelta(days=_KEEP_DAYS)
    for f in _LOG_DIR.glob("cidaren_*.log"):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
        except Exception:
            pass


def _log_file_path() -> Path:
    """返回当天的统一日志文件路径."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    return _LOG_DIR / f"cidaren_{today}.log"


def app_log(tag: str, msg: str) -> None:
    """写入统一日志文件: logs/cidaren_YYYYMMDD.log."""
    _cleanup_dir()
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    try:
        with _log_file_path().open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{tag:{_TAG_WIDTH}s}] {msg}\n")
    except Exception:
        pass


# —— 兼容旧接口 ——

def decoder_log(tag: str, msg: str) -> None:
    """写入统一日志（兼容 decoder 旧接口）."""
    app_log(tag, msg)


def server_log(tag: str, msg: str) -> None:
    """写入统一日志（兼容 server 旧接口）."""
    app_log(tag, msg)


# ── 运行级日志（前端可见 + 统一文件）──────────────────


@dataclass
class WebLogger:
    """运行日志：内存缓冲供前端轮询 + 统一日志文件持久化."""

    task_name: str = ""
    _entries: List[Dict[str, str]] = field(default_factory=list, repr=False)
    _file_path: Optional[Path] = field(default=None, repr=False)
    _topic_total: int = 0
    _done: int = 0
    _mode: int = 0

    def start(self, task_name: str) -> None:
        self.task_name = task_name
        self._entries = []
        self._file("=" * 50)
        self._file(f"任务: {task_name}")
        self._file("=" * 50)

    # ── 前端 + 文件 ──

    def write(self, tag: str, msg: str) -> None:
        """写入内存缓冲（前端可见）+ 统一日志."""
        entry = {"time": _ts(), "tag": tag, "msg": msg}
        self._entries.append(entry)
        if len(self._entries) > _MAX_MEM_LOGS:
            self._entries = self._entries[-_MAX_MEM_LOGS:]
        self._file(f"[{tag:{_TAG_WIDTH}s}] {msg}")

    # ── 仅文件 ──

    def debug(self, msg: str) -> None:
        """仅写入统一日志，不在前端展示，用于调试详情."""
        self._file(f"  > {msg}")

    def debug_api(self, method: str, url: str, params: str = "", body: str = "",
                  status: str = "", response_keys: str = "") -> None:
        parts = [f"{method} {url}"]
        if params:
            parts.append(f"  params={params}")
        if body:
            parts.append(f"  body={body}")
        if status:
            parts.append(f"  → {status}")
        if response_keys:
            parts.append(f"  keys={response_keys}")
        self._file("  ── API ──")
        for p in parts:
            self._file(f"  {p}")

    def debug_solver(self, mode: int, source: str, answer: str, detail: str = "") -> None:
        """记录 solver 选择策略."""
        self._file(f"  ── SOLVER mode={mode} source={source} answer={answer!r}")
        if detail:
            self._file(f"  {detail}")

    def debug_error(self, exc: Exception) -> None:
        """记录完整异常堆栈（仅文件）."""
        self._file(f"  ── ERROR ──")
        self._file(f"  {type(exc).__name__}: {exc}")
        for line in tb.format_exc().splitlines():
            self._file(f"  {line}")

    # ── 前端读取 ──

    def logs(self) -> List[str]:
        return [f"[{e['time']}] [{e['tag']:{_TAG_WIDTH}s}] {e['msg']}" for e in self._entries]

    def clear(self) -> None:
        self._entries.clear()

    # ── 内部 ──

    def _file(self, line: str) -> None:
        """写入统一日志文件."""
        app_log("RUN", line)
