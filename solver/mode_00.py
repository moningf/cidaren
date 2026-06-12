"""Mode 0: 阅读卡片 — 直接翻页，无需答题."""
import time
from typing import Any, Dict

from solver.base import AnswerResult, BaseSolver


class Mode00Solver(BaseSolver):
    source = "pass_through"

    def before_solve(self, api: Any, topic: Dict[str, Any]) -> None:
        time.sleep(1)

    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult:
        return AnswerResult(topic_code=topic.get("topic_code", ""))
