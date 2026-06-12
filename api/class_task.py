"""班级任务相关 API 端点."""
import re
from typing import Any, Dict, Optional

from api.base import BaseAPI

_BASE_URL = "https://app.vocabgo.com/student/api"


def _decode_data(resp: Dict[str, Any]) -> Dict[str, Any]:
    """提取响应中的 data 字段（ResponseDecoder 已完成 jv 层解码）."""
    data = resp.get("data")
    if isinstance(data, dict):
        return data
    return {"code": resp.get("code"), "msg": resp.get("msg")}


def page_task(api: BaseAPI, page_count: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """获取任务列表: POST /Student/ClassTask/PageTask"""
    return api.post(f"{_BASE_URL}/Student/ClassTask/PageTask", {
        "search_type": 0,
        "page_count": page_count,
        "page_size": page_size,
    })


def get_task_info(api: BaseAPI, task_id: Any) -> Dict[str, Any]:
    """获取任务详情: GET /Student/ClassTask/Info"""
    return api.get(f"{_BASE_URL}/Student/ClassTask/Info", params={"task_id": task_id})


def chose_word_list(api: BaseAPI, task_id: Any) -> Dict[str, Any]:
    """选择单词列表展示: GET /Student/ClassTask/ChoseWordList"""
    return api.get(f"{_BASE_URL}/Student/ClassTask/ChoseWordList", params={"task_id": task_id})


def submit_chose_word(api: BaseAPI, task_id: Any, word_map: Dict[str, Any]) -> Dict[str, Any]:
    """提交选词: POST /Student/ClassTask/SubmitChoseWord"""
    return api.post(f"{_BASE_URL}/Student/ClassTask/SubmitChoseWord", {
        "task_id": task_id,
        "word_map": word_map,
        "chose_err_item": 1,
        "reset_chose_words": 1,
        "app_type": 1,
    })


def start_answer(api: BaseAPI, task_id: Any, task_type: Any, release_id: Any) -> Dict[str, Any]:
    """获取题目内容: GET /Student/ClassTask/StartAnswer"""
    resp = api.get(f"{_BASE_URL}/Student/ClassTask/StartAnswer", params={
        "task_id": task_id,
        "task_type": task_type,
        "release_id": release_id,
    })
    return _decode_data(resp)


def submit_answer_and_save(
    api: BaseAPI,
    topic_code: str,
    answer: Any = None,
    app_type: int = 1,
) -> Dict[str, Any]:
    """提交答案: POST /Student/ClassTask/SubmitAnswerAndSave"""
    body: Dict[str, Any] = {
        "topic_code": topic_code,
        "app_type": app_type,
    }
    if answer is not None:
        body["answer"] = answer
    resp = api.post(f"{_BASE_URL}/Student/ClassTask/SubmitAnswerAndSave", body)
    return _decode_data(resp)


def verify_answer(
    api: BaseAPI,
    topic_code: str,
    answer: Any,
    app_type: int = 1,
) -> Dict[str, Any]:
    """验证回答答案: POST /Student/ClassTask/VerifyAnswer"""
    resp = api.post(f"{_BASE_URL}/Student/ClassTask/VerifyAnswer", {
        "answer": answer,
        "topic_code": topic_code,
        "app_type": app_type,
    })
    return _decode_data(resp)


def study_word(api: BaseAPI, course_id: str, list_id: str, word: str) -> Dict[str, Any]:
    """学习单词: GET /Student/Course/StudyWordInfo"""
    resp = api.get(f"{_BASE_URL}/Student/Course/StudyWordInfo", params={
        "course_id": course_id,
        "list_id": list_id,
        "word": word,
    })
    return _decode_data(resp)


def search_word(api: BaseAPI, word: str) -> Optional[str]:
    """查询单词原型: GET /Student/Course/SearchWord"""
    try:
        resp = api.get(f"{_BASE_URL}/Student/Course/SearchWord", params={
            "word": word,
            "version": "2.6.2.24031302",
            "app_type": "1",
        })
        data = _decode_data(resp)
        meaning_str = (data.get("word_mean") or {}).get("meaning", "")
        if meaning_str:
            decoded = bytes(meaning_str, "utf-8").decode("unicode_escape")
            m = re.findall(r"<span>(.+?)</span>", decoded)
            if m:
                return m[0]
    except Exception:
        pass
    return None
