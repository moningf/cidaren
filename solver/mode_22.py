"""Mode 22: 听力题 — 暴力尝试选项 0-3，找正确项."""
import time
from typing import Any, Dict

from solver.base import AnswerResult, BaseSolver


class Mode22Solver(BaseSolver):
    source = "brute_force"

    def before_solve(self, api: Any, topic: Dict[str, Any]) -> None:
        time.sleep(2)

    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult:
        topic_code = topic.get("topic_code", "")

        correct_idx = 0
        for i in range(4):
            res = self.verify_fn(api, topic_code, answer=i)
            if res.get("answer_result") == 1:
                correct_idx = i
                break

        topic_code = res.get("topic_code", topic_code)
        answer_text = ""
        for opt in topic.get("options", []):
            if opt.get("answer_tag") == correct_idx:
                answer_text = opt.get("content", "")
                break

        return AnswerResult(topic_code=topic_code, display=answer_text)
