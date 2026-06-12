"""答题器基类 — 模板方法管道：前置 → 产生答案 → 提交 → 解析下一题."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from api.class_task import submit_answer_and_save as _default_submit, verify_answer as _default_verify
from solver.result import SolveResult


@dataclass
class AnswerResult:
    """produce_answer 的返回值。"""
    topic_code: str = ""   # 当前 topic_code（verify 后可能更新）
    display: str = ""      # 日志展示文本
    source: str = ""       # 答案来源，非空则覆盖类级别 source


class BaseSolver(ABC):
    """答题器基类。

    子类只需实现 produce_answer()，管道自动处理提交和下一题解析。
    如需完全自定义流程，直接覆盖 solve()。

    submit_fn / verify_fn 可由外部设置为自学任务的 API 函数。
    """

    source: str = ""  # 答案来源标识，子类覆盖

    submit_fn = _default_submit
    verify_fn = _default_verify

    # ── 公共管道 ──────────────────────────────

    def solve(self, api: Any, topic: Dict[str, Any]) -> SolveResult:
        self.before_solve(api, topic)
        ar = self.produce_answer(api, topic)
        return self._submit_and_next(api, topic, ar)

    def _submit_and_next(self, api: Any, topic: Dict[str, Any], ar: AnswerResult) -> SolveResult:
        topic_code = ar.topic_code or topic.get("topic_code", "")
        display = ar.display or self._default_display(topic)

        resp = self.submit_fn(api, topic_code)
        nxt = resp if isinstance(resp, dict) and "topic_mode" in resp else None
        return SolveResult(topic=nxt, answer=display, source=ar.source or self.source)

    # ── 子类必须实现 ──────────────────────────

    @abstractmethod
    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult: ...

    # ── 子类可选覆盖 ──────────────────────────

    def before_solve(self, api: Any, topic: Dict[str, Any]) -> None:
        """前置钩子（如延迟、预处理）"""

    def _default_display(self, topic: Dict[str, Any]) -> str:
        return topic.get("stem", {}).get("content", "")
