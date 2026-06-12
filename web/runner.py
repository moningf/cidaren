"""后台任务执行器 — 在独立线程中依次执行多个任务."""
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from api.base import BaseAPI
from api.class_task import chose_word_list, submit_chose_word, start_answer
from api.study_task import (
    study_task_info,
    study_chose_word_list,
    study_submit_chose_word,
    study_start_answer,
    study_submit_answer_and_save,
    study_verify_answer,
)
from decoder.response_decoder import ResponseDecoder
from utils.ai import AIService
from solver.registry import create_registry
from web.logging import WebLogger


@dataclass
class RunnerStatus:
    """共享状态：执行进度 + 日志（带统计）."""

    running: bool = False
    current_task: str = ""
    task_index: int = 0
    total_tasks: int = 0
    topic_done: int = 0
    topic_total: int = 0
    success_count: int = 0
    skip_count: int = 0
    error_count: int = 0
    _logger: WebLogger = field(default_factory=WebLogger, repr=False)

    def reset_stats(self) -> None:
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0

    def log(self, tag: str, msg: str) -> None:
        self._logger.write(tag, msg)

    def logs(self) -> List[str]:
        return self._logger.logs()

    def start_log(self, task_name: str) -> None:
        self._logger.start(task_name)


class TaskRunner:
    """在后台线程中依次执行多个班级任务."""

    def __init__(self, tasks: List[Dict[str, Any]], settings: Dict[str, str]) -> None:
        self._tasks = tasks
        self._settings = settings
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.status = RunnerStatus()
        self.status.total_tasks = len(tasks)

    def start(self) -> None:
        self._stop.clear()
        self.status.running = True
        self.status.reset_stats()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.status.log("RUN", "收到停止信号，当前题目完成后停止")

    def _run(self) -> None:
        total = self.status.total_tasks
        self.status.log("RUN", f"开始执行 {total} 个任务")
        for i, task in enumerate(self._tasks):
            if self._stop.is_set():
                break
            self.status.task_index = i + 1
            self.status.current_task = task.get("task_name", f"任务{i + 1}")
            self.status.start_log(self.status.current_task)
            source = task.get("source", "class")
            uid = task.get("uid", "")
            self.status._logger.debug(f"task[{i}] uid={uid} source={source} type={task.get('task_type')}")
            try:
                self._run_one(task)
            except Exception as exc:
                self.status.error_count += 1
                self.status.log("ERR", f'"{self.status.current_task}" 异常: {exc}')
                self.status._logger.debug_error(exc)
        self.status.running = False
        s, sk, e = self.status.success_count, self.status.skip_count, self.status.error_count
        label = "已停止" if self._stop.is_set() else "全部完成"
        self.status.log("RUN", f"{label}，成功{s} 跳过{sk} 失败{e}")

    def _run_one(self, task: Dict[str, Any]) -> None:
        source = task.get("source", "class")
        if source == "study":
            self._run_study_task(task)
        else:
            self._run_class_task(task)

    def _run_class_task(self, task: Dict[str, Any]) -> None:
        token = self._settings.get("user_token", "")
        ai_key = self._settings.get("deepseek_api_key", "")
        ai_url = self._settings.get("deepseek_base_url", "")
        ai_model = self._settings.get("ai_model", "")

        api = BaseAPI(ResponseDecoder())
        api.set_token(token)

        task_id = task["task_id"]
        task_name = task.get("task_name", "")
        log = self.status._logger

        # ── 选词 + 开始答题 ──
        log.debug_api("GET", "ClassTask/ChoseWordList", params=f"task_id={task_id}")
        wl = chose_word_list(api, task_id)
        wl_data = wl.get("data") or {}
        word_list = wl_data.get("word_list", [])
        course_id = wl_data.get("course_id", "")
        log.debug(f"chose_word_list → course_id={course_id}, {len(word_list)} words: {[w.get('word','') for w in word_list[:5]]}{'...' if len(word_list) > 5 else ''}")

        if not word_list:
            self.status.skip_count += 1
            self.status.log("TASK", f'"{task_name}" 跳过 — 单词列表为空')
            return

        list_id = word_list[0].get("list_id", "") if word_list else ""
        key = f"{course_id}:{list_id}"
        value = [w.get("word", "") for w in word_list]
        log.debug_api("POST", "ClassTask/SubmitChoseWord", body=f"task_id={task_id}, key={key}, words={len(value)}")
        submit_chose_word(api, task_id, {key: value})
        time.sleep(1)

        log.debug_api("GET", "ClassTask/StartAnswer", params=f"task_id={task_id}, task_type={task.get('task_type', 0)}")
        result = start_answer(api, task_id, task.get("task_type", 0), task.get("release_id", ""))
        if not result or "topic_mode" not in result:
            self.status.skip_count += 1
            self.status.log("TASK", f'"{task_name}" 跳过 — 无题目数据')
            log.debug(f"start_answer 返回无 topic_mode: keys={list(result.keys()) if result else 'None'}")
            return

        topic = result
        topic_total = topic.get("topic_total", 0)
        self.status.topic_total = topic_total
        self.status.log("TASK", f'"{task_name}" 准备完成 ({len(word_list)}词)，共 {topic_total} 题')
        log.debug(f"topic_mode={topic.get('topic_mode')}, topic_total={topic_total}, topic_code={str(topic.get('topic_code',''))[:30]}")

        ai = AIService(api_key=ai_key, base_url=ai_url, model=ai_model) if (ai_key or "").strip() else None
        log.debug(f"AI enabled: {ai is not None}")
        solvers = create_registry(course_id, word_list, ai=ai)
        self._answer_loop(api, task_name, topic, topic_total, solvers)

    def _run_study_task(self, task: Dict[str, Any]) -> None:
        token = self._settings.get("user_token", "")
        ai_key = self._settings.get("deepseek_api_key", "")
        ai_url = self._settings.get("deepseek_base_url", "")
        ai_model = self._settings.get("ai_model", "")

        api = BaseAPI(ResponseDecoder())
        api.set_token(token)

        task_name = task.get("task_name", "")
        course_id = task.get("course_id", "CET4_v2")
        list_id = task.get("list_id", "")
        task_type = task.get("task_type", 3)
        log = self.status._logger

        # task_id 初始可能为 -1，通过 study_task_info 获取真实 ID
        task_id = task.get("task_id")
        log.debug_api("GET", "StudyTask/Info", params=f"task_id={task_id}, course_id={course_id}, list_id={list_id}")
        info = study_task_info(api, task_id=task_id, course_id=course_id, list_id=list_id)
        info_data = info.get("data") or {}
        real_task_id = info_data.get("task_id", task_id)
        log.debug(f"study_task_info: task_id {task_id} → {real_task_id}")

        # ── 选词 ──
        log.debug_api("GET", "StudyTask/ChoseWordList", params=f"task_id={real_task_id}, course_id={course_id}, list_id={list_id}")
        wl = study_chose_word_list(api, task_id=real_task_id, course_id=course_id, list_id=list_id)
        word_list = (wl.get("data") or {}).get("word_list", [])
        log.debug(f"chose_word_list → {len(word_list)} words: {[w.get('word','') for w in word_list[:5]]}{'...' if len(word_list) > 5 else ''}")

        if not word_list:
            self.status.skip_count += 1
            self.status.log("TASK", f'"{task_name}" 跳过 — 单词列表为空')
            return

        word_map: Dict[str, list] = {}
        for w in word_list:
            key = f"{w.get('course_id', course_id)}:{w.get('list_id', list_id)}"
            word_map.setdefault(key, []).append(w["word"])
        log.debug_api("POST", "StudyTask/SubmitChoseWord", body=f"task_id={real_task_id}, keys={list(word_map.keys())}")
        study_submit_chose_word(api, task_id=real_task_id, course_id=course_id, list_id=list_id, word_map=word_map)
        time.sleep(1)

        # ── 开始答题 ──
        log.debug_api("GET", "StudyTask/StartAnswer", params=f"task_id={real_task_id}, task_type={task_type}, grade={task.get('grade',2)}")
        topic = study_start_answer(api, task_id=real_task_id, course_id=course_id, list_id=list_id, task_type=task_type)
        if not topic or "topic_mode" not in topic:
            self.status.skip_count += 1
            self.status.log("TASK", f'"{task_name}" 跳过 — 无题目数据')
            log.debug(f"start_answer 返回无 topic_mode: {topic}")
            return

        topic_total = topic.get("topic_total", 0)
        self.status.topic_total = topic_total
        self.status.log("TASK", f'"{task_name}" 准备完成 ({len(word_list)}词)，共 {topic_total} 题')
        log.debug(f"topic_mode={topic.get('topic_mode')}, topic_total={topic_total}, topic_code={str(topic.get('topic_code',''))[:30]}")

        # ── 构建 solver（切换到自学任务 API） ──
        ai = AIService(api_key=ai_key, base_url=ai_url, model=ai_model) if (ai_key or "").strip() else None
        log.debug(f"AI enabled: {ai is not None}")
        solvers = create_registry(course_id, word_list, ai=ai)
        for s in solvers.values():
            s.submit_fn = study_submit_answer_and_save
            s.verify_fn = study_verify_answer

        self._answer_loop(api, task_name, topic, topic_total, solvers)

    def _answer_loop(self, api: BaseAPI, task_name: str, topic: Dict[str, Any],
                     topic_total: int, solvers: Dict[int, Any]) -> None:
        """公共答题循环."""
        answered = 0
        log = self.status._logger
        consecutive_errors = 0
        while topic is not None and "topic_mode" in topic:
            if self._stop.is_set():
                self.status.log("TASK", f'"{task_name}" 已停止 ({answered}/{topic_total})')
                return

            mode = topic.get("topic_mode", 0)
            done = topic.get("topic_done_num", 0)
            self.status.topic_done = done
            answered = done

            solver = solvers.get(mode)
            if solver is None:
                self.status.log("ERR", f'"{task_name}" 未注册 mode={mode}，终止')
                log.debug(f"无 solver 注册 mode={mode}, 可用 modes={list(solvers.keys())}")
                break

            try:
                result = solver.solve(api, topic)
                display = result.answer or ""
                topic_code = str(topic.get("topic_code", ""))[:30]
                log.debug_solver(mode, result.source, display,
                                 f"topic_code={topic_code} topic_done={done}/{topic_total}")
                tag = " [AI]" if result.source == "ai" else ""
                self.status.log("ANS", f"[{done}/{topic_total}] mode={mode} → {display}{tag}")
                topic = result.topic
                consecutive_errors = 0
            except Exception as exc:
                log.debug_error(exc)
                self.status.log("ERR", f"mode={mode} 答题异常: {exc}")
                consecutive_errors += 1
                if consecutive_errors >= 5:
                    log.debug("连续 5 题异常，终止答题")
                    break
                # 尝试跳过当前题继续
                topic_code = topic.get("topic_code", "")
                log.debug(f"跳过 topic_code={str(topic_code)[:30]}, 调用 submit_fn")
                try:
                    topic = self.status._logger  # placeholder, will be set below
                    result = solver.submit_fn(api, topic_code)
                    topic = result if isinstance(result, dict) and "topic_mode" in result else None
                except Exception:
                    topic = None

        self.status.success_count += 1
        self.status.log("TASK", f'"{task_name}" 完成 ({answered}/{topic_total})')
