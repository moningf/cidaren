"""CIDAREN Web 任务面板 — FastAPI 后端."""
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from api.base import BaseAPI, TokenExpiredError
from api.class_task import page_task
from api.study_task import study_task_list
from decoder.response_decoder import ResponseDecoder
from web.runner import TaskRunner
from web.logging import server_log

_SETTINGS_PATH = Path(__file__).parent.parent / "settings.json"
_API_BASE = "https://app.vocabgo.com/student/api"
_DEFAULT_SETTINGS = {
    "user_token": "",
    "deepseek_api_key": "",
    "deepseek_base_url": "https://api.deepseek.com",
    "ai_model": "deepseek-chat",
    "course_id": "CET4_v2",
    "study_grade": "2",
}

app = FastAPI(title="CIDAREN", docs_url=None, redoc_url=None)

_runner: Optional[TaskRunner] = None
_runner_lock = threading.Lock()

_task_cache: Dict[str, tuple[str, List[Dict[str, Any]], float]] = {
    "class": ("", [], 0.0),
    "study": ("", [], 0.0),
}


# ── Token 管理 ──────────────────────────────────────
# 设计：token 一旦被确认为有效，就默认一直可用，不再重复校验。
# 获取优先级：settings.json → 内存扫描 → 提示用户

_known_good_token: Optional[str] = None  # 确认有效的 token，之后永远信任
_memory_token_checked = False


def _validate_token(token: str) -> bool:
    """通过一次 page_task 请求验证 token 是否有效."""
    try:
        api = _create_api(token)
        resp = page_task(api)
        return resp.get("code") == 1
    except Exception:
        return False


def _get_token() -> tuple[str, str, str]:
    """获取 token，返回 (token, error, source)。首次获取会校验 settings 和内存候选。"""
    global _known_good_token

    # 已有确认好用的 token
    if _known_good_token:
        return _known_good_token, "", "known"

    # 1. 优先 settings.json，但需要验证
    manual = _read_settings().get("user_token", "").strip()
    if manual:
        if _validate_token(manual):
            _known_good_token = manual
            return manual, "", "settings"
        # settings 里的 token 无效，清空
        _write_settings({"user_token": ""})

    # 2. 尝试内存扫描
    token = _try_memory_token_once()
    if token:
        _known_good_token = token
        _write_settings({"user_token": token})
        return token, "", "memory"

    # 3. 什么都没有
    return "", "missing", ""


def _try_memory_token_once() -> Optional[str]:
    """尝试从微信进程内存提取 token（仅一次，不校验有效性）."""
    global _memory_token_checked
    if _memory_token_checked:
        return None
    _memory_token_checked = True
    try:
        from auth import get_all_tokens
        candidates = get_all_tokens()
        # 校验直到找到有效的一个（仅此处校验，之后不再校验）
        for t in candidates:
            try:
                api = BaseAPI(ResponseDecoder())
                api.set_token(t)
                resp = page_task(api)
                if resp.get("code") == 1:
                    return t
            except Exception:
                continue
    except Exception:
        pass
    return None


def _reset_memory_scan() -> None:
    """重置内存扫描 + 已信任 token，用于「自动获取」按钮触发重新扫描."""
    global _known_good_token, _memory_token_checked
    _known_good_token = None
    _memory_token_checked = False


def _invalidate_token() -> None:
    """标记当前 token 失效（API 调用返回 401 等场景时调用）."""
    global _known_good_token
    _known_good_token = None


def _create_api(token: str) -> BaseAPI:
    """创建已设置 token 的 BaseAPI，并绑定 token 过期回调."""
    api = BaseAPI(ResponseDecoder())
    api.set_token(token)
    api.on_token_expired = _invalidate_token
    return api


# ── 设置读写 ──────────────────────────────────────

def _read_settings() -> Dict[str, str]:
    if _SETTINGS_PATH.exists():
        try:
            current = dict(_DEFAULT_SETTINGS)
            current.update(json.loads(_SETTINGS_PATH.read_text()))
            return current
        except Exception:
            pass
    return dict(_DEFAULT_SETTINGS)


def _write_settings(data: Dict[str, str]) -> None:
    current = _read_settings()
    current.update(data)
    _SETTINGS_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2))


# ── 任务过期判断 ──────────────────────────────────

def _is_task_expired(task: Dict[str, Any]) -> bool:
    if task.get("over_status") == 3:
        return True
    now_ms = int(time.time() * 1000)
    if (task.get("start_time", 0) + task.get("over_time", 0)) <= now_ms:
        return True
    return False


# ── 任务缓存 ──────────────────────────────────────

def _merge_tasks(cached: List[Dict[str, Any]], fresh: List[Dict[str, Any]],
                 source: str) -> List[Dict[str, Any]]:
    """将 fresh 中的进度/得分合并到 cached 中，保留 cached 的其他字段."""
    fresh_by_uid = {t["uid"]: t for t in fresh}
    merged = []
    for t in cached:
        f = fresh_by_uid.pop(t["uid"], None)
        if f is not None:
            t["progress"] = f["progress"]
            t["score"] = f["score"]
            if source == "class":
                t["over_status"] = f.get("over_status", t.get("over_status", 0))
                t["expired"] = _is_task_expired(t)
        merged.append(t)
    # 新出现的任务直接追加
    for f in fresh_by_uid.values():
        if source == "class":
            f["expired"] = _is_task_expired(f)
        else:
            f["expired"] = False
        merged.append(f)
    return merged


def _get_cached_tasks(token: str, course_id: str, force: bool = False, source: str = "") -> List[Dict[str, Any]]:
    """返回任务列表。缓存永久有效（同 token），force=True 时合并进度/得分。

    source: "class" 只拉班级任务, "study" 只拉自学任务, "" 拉全部.
    """
    global _task_cache

    if source in ("class", "study"):
        prev_token, prev_tasks, _ = _task_cache[source]
        if prev_token != token:
            # token 变了，全量刷新
            if source == "class":
                tasks = _fetch_all_tasks(token)
                for t in tasks:
                    t["expired"] = _is_task_expired(t)
            else:
                tasks = _fetch_study_tasks(token, course_id)
                for t in tasks:
                    t["expired"] = False
            _task_cache[source] = (token, tasks, time.time())
            return tasks
        if not force:
            return prev_tasks
        # force=True: 只合并进度和得分
        if source == "class":
            fresh = _fetch_all_tasks(token)
        else:
            fresh = _fetch_study_tasks(token, course_id)
        merged = _merge_tasks(prev_tasks, fresh, source)
        _task_cache[source] = (token, merged, time.time())
        return merged

    # 全量请求
    c_token, c_tasks, _ = _task_cache["class"]
    s_token, s_tasks, _ = _task_cache["study"]
    if c_token == token and s_token == token:
        if not force:
            return c_tasks + s_tasks
        # force=True: 合并两个源的进度/得分
        c_fresh = _fetch_all_tasks(token)
        s_fresh = _fetch_study_tasks(token, course_id)
        c_merged = _merge_tasks(c_tasks, c_fresh, "class")
        s_merged = _merge_tasks(s_tasks, s_fresh, "study")
        _task_cache["class"] = (token, c_merged, time.time())
        _task_cache["study"] = (token, s_merged, time.time())
        return c_merged + s_merged
    # token 变了，全量刷新
    tasks = _fetch_all_tasks(token)
    study_tasks = _fetch_study_tasks(token, course_id)
    for t in tasks:
        t["expired"] = _is_task_expired(t)
    for t in study_tasks:
        t["expired"] = False
    _task_cache["class"] = (token, tasks, time.time())
    _task_cache["study"] = (token, study_tasks, time.time())
    return tasks + study_tasks


# ── 任务获取 ──────────────────────────────────────

def _fetch_all_tasks(token: str) -> List[Dict[str, Any]]:
    """拉取班级任务."""
    api = _create_api(token)
    all_tasks: List[Dict[str, Any]] = []
    page = 1
    while True:
        resp = page_task(api, page_count=page, page_size=20)
        data = resp.get("data") or {}
        records = data.get("records", [])
        if not records:
            break
        for t in records:
            all_tasks.append({
                "uid": f"class:{t.get('task_id', '')}",
                "source": "class",
                "task_id": t.get("task_id", ""),
                "task_name": t.get("task_name", ""),
                "task_type": t.get("task_type", 0),
                "progress": t.get("progress", 0),
                "score": t.get("score", 0),
                "over_status": t.get("over_status", 0),
                "start_time": t.get("start_time", 0),
                "over_time": t.get("over_time", 0),
                "release_id": t.get("release_id", ""),
            })
        total = data.get("total", 0)
        if len(all_tasks) >= total:
            break
        page += 1
    return all_tasks


def _fetch_study_tasks(token: str, course_id: str) -> List[Dict[str, Any]]:
    """拉取自学任务."""
    api = _create_api(token)
    try:
        resp = study_task_list(api, course_id=course_id)
        task_list = (resp.get("data") or {}).get("task_list", [])
    except Exception:
        return []
    return [{
        "uid": f"study:{t.get('list_id', '')}",
        "source": "study",
        "task_id": t.get("task_id", -1),
        "task_name": t.get("task_name", t.get("list_id", "")),
        "task_type": t.get("task_type", 3),
        "progress": t.get("progress", 0),
        "score": t.get("score", 0),
        "start_time": 0,
        "over_time": 0,
        "course_id": t.get("course_id", course_id),
        "list_id": t.get("list_id", ""),
        "grade": t.get("grade", 2),
    } for t in task_list]


# ── API 端点 ─────────────────────────────────────

class RunRequest(BaseModel):
    task_ids: List[str]
    tasks: List[Dict[str, Any]] = []


class SettingsRequest(BaseModel):
    user_token: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-chat"
    course_id: str = "CET4_v2"
    study_grade: str = "2"


@app.get("/", response_class=HTMLResponse)
async def main_page():
    template = Path(__file__).parent / "templates" / "dashboard.html"
    if template.exists():
        return HTMLResponse(template.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>dashboard.html 未找到</h1>", status_code=404)


@app.get("/api/tasks")
async def api_tasks(force: bool = False, source: str = ""):
    token, error, _source = _get_token()
    if error == "missing":
        return JSONResponse({"error": "未获取到 Token，请确保微信已打开词达人或在设置中手动输入"}, status_code=400)
    try:
        settings = _read_settings()
        course_id = settings.get("course_id", "CET4_v2")
        all_tasks = _get_cached_tasks(token, course_id, force=force, source=source)
        class_n = sum(1 for t in all_tasks if t["source"] == "class")
        study_n = sum(1 for t in all_tasks if t["source"] == "study")
        server_log("API", f"/api/tasks → {len(all_tasks)} tasks (class={class_n}, study={study_n})"
                   + (f" source={source}" if source else ""))
        return {"tasks": all_tasks}
    except TokenExpiredError:
        server_log("TOKEN", "settings 中的 token 已过期")
        return JSONResponse({"error": "TOKEN_EXPIRED", "message": "当前 Token 已过期，请重新获取或手动设置"}, status_code=401)
    except Exception as exc:
        server_log("ERR", f"/api/tasks 失败: {exc}")
        return JSONResponse({"error": f"获取任务失败: {exc}"}, status_code=500)


@app.get("/api/status")
async def api_status():
    global _runner
    with _runner_lock:
        r = _runner
    if r is None:
        return {"running": False, "current_task": "", "task_index": 0, "total_tasks": 0,
                "topic_done": 0, "topic_total": 0, "pending": [], "logs": []}
    # 待执行任务队列（含当前任务），task_index 是 1-based
    idx = max(0, r.status.task_index - 1)
    pending = [t.get("task_name", "") for t in r._tasks[idx:]]
    return {
        "running": r.status.running,
        "current_task": r.status.current_task,
        "task_index": r.status.task_index,
        "total_tasks": r.status.total_tasks,
        "topic_done": r.status.topic_done,
        "topic_total": r.status.topic_total,
        "pending": pending,
        "logs": r.status.logs()[-50:],
    }


@app.post("/api/run")
async def api_run(req: RunRequest):
    global _runner
    try:
        with _runner_lock:
            if _runner is not None and _runner.status.running:
                raise HTTPException(400, "已有任务正在执行")
            token, error, _source = _get_token()
            if error == "missing":
                raise HTTPException(400, "未获取到 Token，请确保微信已打开词达人或在设置中手动输入")
            settings = _read_settings()
            # 优先使用前端传来的任务数据，避免重复拉取
            if req.tasks:
                selected = req.tasks
            else:
                course_id = settings.get("course_id", "CET4_v2")
                all_tasks = _get_cached_tasks(token, course_id)
                task_by_uid = {t["uid"]: t for t in all_tasks}
                selected = []
                for uid in req.task_ids:
                    t = task_by_uid.get(uid)
                    if t is None:
                        raise HTTPException(400, f"任务 {uid} 未找到")
                    if t.get("source") == "class" and t.get("expired"):
                        raise HTTPException(400, f"任务 '{t['task_name']}' 已过期，无法执行")
            if not selected:
                raise HTTPException(400, "未选择有效任务")
            _runner = TaskRunner(selected, settings)
    except TokenExpiredError:
        server_log("TOKEN", "settings 中的 token 已过期")
        raise HTTPException(401, "当前 Token 已过期，请重新获取或手动设置")
    _runner.start()
    server_log("RUN", f"启动 {len(selected)} 个任务: {[t['task_name'] for t in selected]}")
    return {"status": "started", "count": len(selected)}


@app.post("/api/stop")
async def api_stop():
    global _runner
    with _runner_lock:
        r = _runner
    if r is None:
        return {"status": "no_task"}
    r.stop()
    return {"status": "stopping"}


class AiTestRequest(BaseModel):
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"


@app.post("/api/ai/test")
async def api_test_ai(req: AiTestRequest):
    key = req.api_key.strip()
    if not key:
        return {"ok": False, "message": "API Key 为空"}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key, base_url=req.base_url)
        resp = client.chat.completions.create(
            model=req.model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        reply = resp.choices[0].message.content
        server_log("AI_TEST", f"model={req.model} url={req.base_url} → ok: {reply}")
        return {"ok": True, "message": f"模型 {req.model} 响应正常"}
    except Exception as exc:
        server_log("AI_TEST", f"model={req.model} url={req.base_url} → fail: {exc}")
        return {"ok": False, "message": str(exc)}


@app.get("/api/token")
async def api_get_token():
    """获取有效 token：先验证 settings，不行则内存扫描，成功后写入 settings."""
    token, error, source = _get_token()
    if error == "missing":
        return {"found": False}
    server_log("TOKEN", f"token 来源: {source}")
    return {"found": True, "source": source}


@app.get("/api/token/scan")
async def api_scan_token():
    """主动触发内存扫描获取 token，返回结果."""
    _reset_memory_scan()
    token = _try_memory_token_once()
    if token:
        global _known_good_token
        _known_good_token = token
        _write_settings({"user_token": token})
        server_log("TOKEN", "内存扫描成功，获取到有效 token")
        return {"found": True, "source": "memory"}
    # 回退到 settings
    manual = _read_settings().get("user_token", "").strip()
    if manual:
        _known_good_token = manual
        server_log("TOKEN", "使用 settings.json 中的 token")
        return {"found": True, "source": "settings"}
    server_log("TOKEN", "未找到有效 token")
    return {"found": False}


@app.get("/api/settings")
async def api_get_settings():
    return _read_settings()


@app.post("/api/settings")
async def api_save_settings(req: SettingsRequest):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    _write_settings(data)
    # 如果 token 被修改，重置已信任 token，下次请求会重新验证 settings 里的 token
    if "user_token" in data:
        global _known_good_token
        _known_good_token = None
    return {"status": "saved"}
