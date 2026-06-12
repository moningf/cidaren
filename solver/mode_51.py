"""Mode 51: 翻译填空 — 通过 w_tip + w_len 从单词列表查找."""
from typing import Any, Dict, TYPE_CHECKING

from utils.vocab import VocabService
from solver.base import AnswerResult, BaseSolver

if TYPE_CHECKING:
    from utils.ai import AIService


class Mode51Solver(BaseSolver):
    source = "word_list"

    def __init__(self, vocab: VocabService, ai: "AIService | None" = None) -> None:
        self._vocab = vocab
        self._ai = ai

    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult:
        topic_code = topic.get("topic_code", "")
        w_tip = topic.get("w_tip", "")
        w_len = topic.get("w_len", 0)

        answer = ""
        if w_tip and w_len:
            answer = self._vocab.find_by_prefix_len(w_tip, w_len) or ""

        if answer:
            res = self.verify_fn(api, topic_code, answer=answer)
            return AnswerResult(
                topic_code=res.get("topic_code", topic_code),
                display=answer,
                source="word_list",
            )

        # AI 兜底
        if self._ai is not None:
            result = self._ai.answer_for_51(topic)
            ai_answer = result.get("answer", "")
            if ai_answer:
                res = self.verify_fn(api, topic_code, answer=ai_answer)
                return AnswerResult(
                    topic_code=res.get("topic_code", topic_code),
                    display=ai_answer,
                    source="ai",
                )

        return AnswerResult(topic_code=topic_code, display="(无匹配)")
