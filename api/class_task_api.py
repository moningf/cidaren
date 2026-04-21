def page_task(client):
    """获取任务列表: POST /Student/ClassTask/PageTask"""
    url = "/Student/ClassTask/PageTask"
    body = {}
    return client.post(url, body)


def get_task_info(client,task_id):
    """获取任务详情: GET /Student/ClassTask/Info"""
    url = "/Student/ClassTask/Info"
    params = {
        "task_id": task_id
    }
    return client.get(url, params=params)


def chose_word_list(client,task_id):
    """选择单词列表展示: GET /Student/ClassTask/ChoseWordList"""
    url = "/Student/ClassTask/ChoseWordList"
    params = {
        "task_id": task_id
    }
    return client.get(url, params=params)


def submit_chose_word(client,task_id,word_map: dict):
    """提交选词: POST /Student/ClassTask/SubmitChoseWord"""
    url = "/Student/ClassTask/SubmitChoseWord"
    body = {
        "task_id": task_id,
        "word_map": word_map,
        "chose_err_item": 1,
        "reset_chose_words": 1,
        "app_type": 1,
    }
    return client.post(url, body)


def start_answer(client,task_id,task_type,release_id,):
    """获取题目内容: GET /Student/ClassTask/StartAnswer"""
    url = "/Student/ClassTask/StartAnswer"
    params = {
        "task_id": task_id,
        "task_type": task_type,
        "release_id": release_id,
    }
    return client.get(url, params=params)


def submit_answer_and_save(
    client,
    topic_code,
    answer=None,
    app_type=1,
):
    """提交答案: POST /Student/ClassTask/SubmitAnswerAndSave"""
    url = "/Student/ClassTask/SubmitAnswerAndSave"
    body = {
        "topic_code": topic_code,
        "app_type": app_type,
    }
    options = {
        "answer": answer,
    }
    for key, value in options.items():
        if value is not None:
            body[key] = value
    return client.post(url, body)


def verify_answer(client, topic_code, answer, app_type=1):
    """验证回答答案: POST /Student/ClassTask/VerifyAnswer"""
    url = "/Student/ClassTask/VerifyAnswer"
    body = {
        "answer": answer,
        "topic_code": topic_code,
        "app_type": app_type,
    }
    return client.post(url, body)

def study_word(client,course_id,list_id,word):
    url = "/Student/Course/StudyWordInfo"
    params = {
        "course_id": course_id,
        "list_id": list_id,
        "word": word,
    }
    return client.get(url, params=params)