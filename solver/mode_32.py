"""Mode 32: 翻译题 — 通过 StudyWordInfo 短语匹配确定选项词和顺序."""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from utils.vocab import VocabService, _normalize_cn, is_common_word, clean_phrase
from solver.base import AnswerResult, BaseSolver

if TYPE_CHECKING:
    from utils.ai import AIService


def _cn_match_score(remark: str, cn: str) -> int:
    """比较中文释义，返回匹配分数：2=精确匹配，1=子串匹配，0=不匹配."""
    r = _normalize_cn(remark)
    c = _normalize_cn(cn)
    if not r or not c:
        return 0
    if r == c:
        return 2
    shorter = min(r, c, key=len)
    longer = c if shorter == r else r
    if len(shorter) >= min(len(longer), 4) and shorter in longer:
        return 1
    return 0


def _find_phrase_match(word_result: Dict[str, Any], remark: str) -> tuple[str, int]:
    """在 StudyWordInfo 返回中查找与 remark 匹配的短语/例句.

    返回 (英文内容, 匹配分数): 2=精确, 1=子串, 0=未找到.
    """
    if not remark:
        return "", 0

    means = word_result.get("means", [])
    for m in means:
        for usage in m.get("usages", []):
            for pi in usage.get("phrases_infos", []):
                cn = pi.get("sen_mean_cn", "")
                score = _cn_match_score(remark, cn)
                if score > 0:
                    return pi.get("sen_content", ""), score
            for ex in usage.get("examples", []):
                cn = ex.get("sen_mean_cn", "")
                score = _cn_match_score(remark, cn)
                if score > 0:
                    return ex.get("sen_content", ""), score

    options = word_result.get("options", [])
    for opt in options:
        content = opt.get("content", {})
        for ui in content.get("usage_infos", []):
            cn = ui.get("sen_mean_cn", "")
            score = _cn_match_score(remark, cn)
            if score > 0:
                return ui.get("sen_content", ""), score
        for ex in content.get("example", []):
            cn = ex.get("sen_mean_cn", "")
            score = _cn_match_score(remark, cn)
            if score > 0:
                return ex.get("sen_content", ""), score

    return "", 0


class Mode32Solver(BaseSolver):
    source = "vocab_match"

    def __init__(self, vocab: VocabService, ai: "AIService | None" = None) -> None:
        self._vocab = vocab
        self._ai = ai

    def produce_answer(self, api: Any, topic: Dict[str, Any]) -> AnswerResult:
        topic_code = topic.get("topic_code", "")
        remark = topic.get("stem", {}).get("remark", "")
        options = topic.get("options", [])

        # Step 1 — 精确匹配：找到某个词的短语与 remark 吻合，提交清洗后的短语文本
        best_phrase = ""
        best_score = (-1, 0)  # (cn_match_score, option_word_count)
        for opt in options:
            word = opt.get("content", "")
            result = self._vocab.lookup(api, word)
            if result is None:
                continue
            phrase, cn_score = _find_phrase_match(result, remark)
            if phrase and cn_score == 2:  # 仅信任精确匹配
                # 统计短语中包含的选项词数
                clean = phrase.replace("{", "").replace("}", "")
                tokens = set(clean.lower().split())
                opt_set = {w.strip(".?").lower() for w in [o.get("content", "") for o in options]}
                matched = len(tokens & opt_set)
                cur = (cn_score, matched)
                if cur > best_score:
                    best_score = cur
                    best_phrase = phrase

        if best_phrase:
            answer = clean_phrase(best_phrase)
            res = self.verify_fn(api, topic_code, answer=answer)
            return AnswerResult(
                topic_code=res.get("topic_code", topic_code),
                display=answer,
                source="phrase_match",
            )

        # Step 2 — 回退：保留词表中查得到的词 + 常见功能词
        selected = []
        for opt in options:
            word = opt.get("content", "")
            if self._vocab.lookup(api, word) is not None or is_common_word(word):
                selected.append(word)

        if selected:
            answer = ",".join(selected)
            res = self.verify_fn(api, topic_code, answer=answer)
            return AnswerResult(
                topic_code=res.get("topic_code", topic_code),
                display=answer,
                source="vocab_match",
            )

        # Step 3 — AI 兜底
        if self._ai is not None:
            result = self._ai.answer_for_32(topic)
            ai_answer = result.get("answer", "")
            if ai_answer:
                res = self.verify_fn(api, topic_code, answer=ai_answer)
                return AnswerResult(
                    topic_code=res.get("topic_code", topic_code),
                    display=ai_answer,
                    source="ai",
                )

        return AnswerResult(topic_code=topic_code, display="(无匹配)")
