##TODO 当前接口暂未完善，后续根据需要参数和返回值的处理
def get_study_word_info(
    client,
    topic_code,
    timestamp=None,
    version=None,
    sign=None,
    app_type=1,
    **extra,
):
    """获取当前学习单词详情: POST /Student/Course/GetStudyWordInfo"""
    url = "/Student/Course/GetStudyWordInfo"
    body = {
        "topic_code": topic_code,
        "app_type": app_type,
    }
    if version is not None:
        body["version"] = version
    if sign is not None:
        body["sign"] = sign
    body.update(extra)
    return client.post(url, body)
