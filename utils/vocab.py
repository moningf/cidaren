"""VocabGo 单词查询服务 — 通过 StudyWordInfo API 查词并匹配中文释义."""
import re
from typing import Any, Dict, List, Optional

from api.base import BaseAPI
from api.class_task import study_word, search_word

# 常见功能词/缩略词，不在词表中但频繁出现于翻译题选项
_COMMON_WORDS = frozenset({
    # 缩略/所有格
    "sb.", "sth.", "one's", "sb", "sth", "ones", "one", "oneself",
    # 冠词
    "the", "a", "an",
    # 介词
    "on", "in", "at", "of", "to", "for", "with", "by", "from",
    "out", "off", "up", "down", "over", "under", "into", "onto",
    "against", "between", "among", "during", "before", "after",
    "along", "around", "about", "above", "across", "away",
    "through", "within", "without", "upon", "behind", "beyond",
    # 连词
    "and", "or", "but", "so", "as", "if", "nor", "yet", "than",
    # 限定词/代词
    "no", "not", "yes", "all", "any", "some", "each", "every",
    "both", "few", "many", "much", "such", "other", "another",
    "that", "this", "these", "those",
    # 代词
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    # 常用动词原形
    "is", "be", "are", "was", "were", "been", "being",
    "do", "does", "did", "have", "has", "had", "having",
    "can", "could", "will", "would", "shall", "should",
    "may", "might", "must",
    # 缩写
    "don't", "doesn't", "isn't", "aren't", "wasn't",
    "weren't", "won't", "can't", "couldn't", "wouldn't",
    "shouldn't", "mustn't", "it's", "there's",
    "i'm", "you're", "he's", "she's", "we're", "they're",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
})


def _normalize_cn(text: str) -> str:
    """规范化中文文本：去空白、去尾部省略号和标点."""
    t = text.strip().rstrip("…...。.!！?？~～")
    return re.sub(r"\s+", "", t)


def is_common_word(word: str) -> bool:
    """检查单词是否为常见功能词/缩略词（不在词表中但可用于翻译题）."""
    return word.strip(".?").lower() in {w.strip(".?").lower() for w in _COMMON_WORDS}


# ── 词形还原（规则优先，API 兜底）─────────────────────────────

_RULE_LEMMA = [
    (re.compile(r"(?i)(.+)ying$"), r"\1ie"),   # dying → die
    (re.compile(r"(?i)(.+)ies$"), r"\1y"),      # territories → territory
    (re.compile(r"(?i)(.+)ves$"), r"\1fe"),     # wolves → wolf
    (re.compile(r"(?i)(.+)ses$"), r"\1s"),      # classes → class
    (re.compile(r"(?i)(.+)ied$"), r"\1y"),      # carried → carry
    (re.compile(r"(?i)(.+)est$"), r"\1"),        # biggest → big
    (re.compile(r"(?i)(.+)er$"), r"\1"),         # bigger → big
    (re.compile(r"(?i)(.+)ing$"), r"\1"),        # denying → deny, walking → walk
    (re.compile(r"(?i)(.+)ing$"), r"\1e"),       # making → make
    (re.compile(r"(?i)(.+)ed$"), r"\1"),         # walked → walk
    (re.compile(r"(?i)(.+)ed$"), r"\1e"),        # moved → move
    (re.compile(r"(?i)(.+)es$"), r"\1"),         # teaches → teach
    (re.compile(r"(?i)(.+)s$"), r"\1"),          # cats → cat
]


def _rule_revert(word: str) -> List[str]:
    """规则法词形还原，返回候选原型列表."""
    candidates: List[str] = []
    for pat, repl in _RULE_LEMMA:
        result = pat.sub(repl, word)
        if result != word and len(result) >= 2:
            candidates.append(result)
    return candidates


# ── 短语清洗 ─────────────────────────────────────────────

def clean_phrase(phrase: str) -> str:
    """清洗短语文本：去 { } 和 …/...，空格换逗号."""
    result = phrase.replace("{", "").replace("}", "")
    result = result.replace(" …", "").replace(" ...", "")
    return result.replace(" ", ",")


def _find_list_id(word: str, word_list: List[Dict[str, Any]]) -> str:
    """从单词列表中找到该词对应的 list_id."""
    for w in word_list:
        if w.get("word") == word:
            return w.get("list_id", "")
    return ""


class VocabService:
    """封装单词查询，用于 mode 32/51 的非 AI 答题。"""

    def __init__(self, course_id: str, word_list: List[Dict[str, Any]]) -> None:
        self._course_id = course_id
        self._word_list = word_list
        self._cache: Dict[str, Dict[str, Any]] = {}

    def lookup(self, api: BaseAPI, word: str) -> Optional[Dict[str, Any]]:
        """查询单词信息（带缓存），查不到时尝试词形还原."""
        cleaned = word.strip(".?")
        if cleaned in self._cache:
            return self._cache[cleaned]

        def _try(w: str) -> Optional[Dict[str, Any]]:
            list_id = _find_list_id(w, self._word_list)
            if not list_id:
                return None
            try:
                return study_word(api, self._course_id, list_id, w)
            except Exception:
                return None

        result = _try(cleaned)
        if result is not None:
            self._cache[cleaned] = result
            return result

        # 词形还原：API 优先
        base = search_word(api, cleaned)
        if base and base != cleaned:
            result = _try(base)
            if result is not None:
                self._cache[cleaned] = result
                return result

        # 规则法兜底
        for candidate in _rule_revert(cleaned):
            if candidate == cleaned:
                continue
            result = _try(candidate)
            if result is not None:
                self._cache[cleaned] = result
                return result

        return None

    def find_by_prefix_len(self, tip: str, word_len: int) -> Optional[str]:
        """按前缀和长度从单词列表中查找（mode 51）."""
        tip_lower = tip.lower()
        for w in self._word_list:
            word = w.get("word", "")
            if word.lower().startswith(tip_lower) and len(word) == word_len:
                return word
        return None
