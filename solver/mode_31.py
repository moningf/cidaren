"""Mode 31: 选词题 — 从 stem.remark 匹配选项内容."""
from typing import Any, Dict, List

from solver.base import AnswerResult, BaseSolver


class Mode31Solver(BaseSolver):
    source = "remark_match"

    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult:
        topic_code = topic.get("topic_code", "")
        answer_tags = self._select(topic)
        count = topic.get("answer_num", 1)

        for i in range(min(count, len(answer_tags))):
            res = self.verify_fn(api, topic_code, answer=int(answer_tags[i]))
            topic_code = res.get("topic_code", topic_code)

        answer_text = ",".join(
            opt.get("content", "")
            for a in answer_tags
            for opt in topic.get("options", [])
            if str(opt.get("answer_tag")) == str(a)
        )
        return AnswerResult(topic_code=topic_code, display=answer_text)

    @staticmethod
    def _select(topic: Dict[str, Any]) -> List[str]:
        stem = topic.get("stem", {})
        remark = stem.get("remark", "")
        if isinstance(remark, list):
            targets = [x.get("relation", "") for x in remark]
        else:
            targets = [remark] if remark else []

        opts = topic.get("options", [])
        return [str(opt.get("answer_tag", 0)) for opt in opts if opt.get("content") in targets]
