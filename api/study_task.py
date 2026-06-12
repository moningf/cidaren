"""自学任务相关 API 端点 — 返回格式与 class_task 保持一致."""
from typing import Any, Dict, Optional

from api.base import BaseAPI

_BASE_URL = "https://app.vocabgo.com/student/api"


def _get_study_topic(resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从 API 响应中提取题目对象，参考 LangQi99 的 _get_topic."""
    d = (resp or {}).get("data") or {}
    if isinstance(d, dict) and d.get("topic_code"):
        return d
    return d.get("topic_info") or d.get("topic") or (d.get("topic_list") or [None])[0]


# ── 任务列表 / 信息 ──

def study_task_list(api: BaseAPI, course_id: str = "CET4_v2") -> Dict[str, Any]:
    """获取自学任务列表: GET /Student/StudyTask/List"""
    return api.get(f"{_BASE_URL}/Student/StudyTask/List", params={"course_id": course_id})


def study_task_info(api: BaseAPI, task_id: Any, course_id: str, list_id: str,
                    task_type: int = 3, grade: int = 2) -> Dict[str, Any]:
    """获取自学任务详情: GET /Student/StudyTask/Info"""
    return api.get(f"{_BASE_URL}/Student/StudyTask/Info", params={
        "task_id": task_id, "course_id": course_id, "list_id": list_id,
        "task_type": task_type, "grade": grade,
    })


# ── 选词 ──

def study_chose_word_list(api: BaseAPI, task_id: Any, course_id: str, list_id: str,
                          task_type: int = 3, grade: int = 2) -> Dict[str, Any]:
    """自学任务选词列表: GET /Student/StudyTask/ChoseWordList"""
    return api.get(f"{_BASE_URL}/Student/StudyTask/ChoseWordList", params={
        "task_id": task_id, "course_id": course_id, "list_id": list_id,
        "task_type": task_type, "grade": grade,
    })


def study_submit_chose_word(api: BaseAPI, task_id: Any, course_id: str, list_id: str,
                            word_map: Dict[str, Any], task_type: int = 3,
                            grade: int = 2) -> Dict[str, Any]:
    """提交自学任务选词: POST /Student/StudyTask/SubmitChoseWord"""
    return api.post(f"{_BASE_URL}/Student/StudyTask/SubmitChoseWord", {
        "task_id": task_id, "task_type": task_type, "grade": grade,
        "course_id": course_id, "list_id": list_id,
        "word_map": word_map, "chose_err_item": 1, "reset_chose_words": 1,
    })


# ── 答题（返回格式与 class_task 保持一致：直接返回题目/结果对象） ──

def study_start_answer(api: BaseAPI, task_id: Any, course_id: str, list_id: str,
                       task_type: int = 3, grade: int = 2) -> Dict[str, Any]:
    """获取自学任务题目: GET /Student/StudyTask/StartAnswer

    返回题目对象(含 topic_code/topic_mode 等)，与 class 版本行为一致。
    """
    resp = api.get(f"{_BASE_URL}/Student/StudyTask/StartAnswer", params={
        "task_id": task_id, "task_type": task_type, "grade": grade,
        "course_id": course_id, "list_id": list_id,
        "opt_img_w": 2300, "opt_font_size": 128, "opt_font_c": "#000000",
        "it_img_w": 2702, "it_font_size": 144,
    })
    return _get_study_topic(resp)


def study_verify_answer(api: BaseAPI, topic_code: str, answer: Any) -> Dict[str, Any]:
    """验证自学任务答案: POST /Student/StudyTask/VerifyAnswer

    返回 verify 结果对象(含 topic_code/answer_result 等)，与 class 版本行为一致。
    """
    resp = api.post(f"{_BASE_URL}/Student/StudyTask/VerifyAnswer", {
        "topic_code": topic_code, "answer": answer,
    })
    return resp.get("data") or resp


def study_submit_answer_and_save(api: BaseAPI, topic_code: str,
                                  time_spent: int = 2000) -> Dict[str, Any]:
    """提交并保存自学任务答案: POST /Student/StudyTask/SubmitAnswerAndSave

    返回下一题对象(含 topic_code/topic_mode 等)，与 class 版本行为一致。
    """
    resp = api.post(f"{_BASE_URL}/Student/StudyTask/SubmitAnswerAndSave", {
        "topic_code": topic_code, "time_spent": time_spent,
        "opt_img_w": 2300, "opt_font_size": 128, "opt_font_c": "#000000",
        "it_img_w": 2702, "it_font_size": 144,
    })
    return _get_study_topic(resp)
