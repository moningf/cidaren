"""DeepSeek AI 答题服务."""
import json
from typing import Any, Dict

from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


class AIService:
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "") -> None:
        key = (api_key or "").strip() or DEEPSEEK_API_KEY
        url = (base_url or "").strip() or DEEPSEEK_BASE_URL
        self._model = (model or "").strip() or "deepseek-chat"
        self._available = bool(key)
        self._client = None
        if self._available:
            self._client = OpenAI(api_key=key, base_url=url)

    def _get_answer(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not self._available:
            return {}
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content or "{}")
        except Exception:
            self._available = False
            return {}

    def answer_for_32(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """32 题型：翻译题，返回逗号分隔的单词字符串."""
        system_prompt = """
请根据以下翻译题内容，从选项中返回正确的英文单词，返回 JSON 数组。
注意: 1. 每个"_"为一个单词（重要!!! 不可少选，不可多选）
      2. 答案为一个字符串的形式，单词之间用逗号分隔。
      3. 回答要按顺序返回正确的单词。
Example:
{"content":"_  ...    _  _","remark": "把......强加给某人","options": ["sb.","on","enforce","acid"]}

Answer:
{"answer": "enforce,on,sb."}
"""
        question = {
            "content": topic["stem"]["content"],
            "remark": topic["stem"]["remark"],
            "options": [opt["content"] for opt in topic["options"]],
        }
        return self._get_answer(system_prompt, str(question))

    def answer_for_51(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """51 题型：翻译填空题，返回单个单词."""
        system_prompt = """
请根据以下翻译填空题内容，返回正确的英文单词，返回 JSON 数组。
Example:
{"content":"be  {}  to  a  higher  rank","remark": "晋级","word_len": 8,"word_tip": "ele"}

Answer:
{"answer": "elevated"}
"""
        question = {
            "content": topic["stem"]["content"],
            "remark": topic["stem"]["remark"],
            "word_len": topic.get("w_len", 0),
            "word_tip": topic.get("w_tip", ""),
        }
        return self._get_answer(system_prompt, str(question))
