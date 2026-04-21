from api import deepseek_api

def answerfor31(topic):
    """31题型专用AI答题"""
    system_prompt = """
请根据以下每道题的题目内容，从选项中选择正确的英文单词对应的序号，返回 JSON 数组。
注意:   1. 每个'_'为一个选项（重要!!！不可少选，不可多选）
        2. 选项下标从0开始。
Example:
{"content":"_ _","remark": "职业展望","options": ["envy","outlook","career","rage"]}

Answer:
{
"answer": [2,1]
}
"""
    question = {
    "content": topic["stem"]["content"],
    "remark": topic["stem"]["remark"],
    "options": [option["content"] for option in topic["options"]]
    }
    options = topic["options"]
    answer = deepseek_api.get_answer(system_prompt, str(question))
    return answer

def answerfor32(topic):
    """32题型专用AI答题"""
    system_prompt = """
请根据以下翻译题内容，从选项中返回正确的英文单词，返回 JSON 数组。
注意: 1. 每个'_'为一个单词（重要!!！不可少选，不可多选）
    2. 答案为一个字符串的形式，单词之间用逗号分隔。
    3. 回答要安装顺序返回正确的单词。
Example:
{"content":"_  ...    _  _","remark": "把......强加给某人","options": ["sb.","on","enforce","acid"]}

Answer:
{
"answer": "enforce,on,sb."
}
"""
    question = {
    "content": topic["stem"]["content"],
    "remark": topic["stem"]["remark"],
    "options": [option["content"] for option in topic["options"]]
    }
    options = topic["options"]
    answer = deepseek_api.get_answer(system_prompt, str(question))
    return answer

def answerfor51(topic):
    """51题型专用AI答题"""
    system_prompt = """
请根据以下翻译填空题内容，返回正确的英文单词，返回 JSON 数组。
Example:
{"content":"be  {}  to  a  higher  rank","remark": "晋级",word_len: 8,word_tip: "ele"}

Answer:
{
"answer": "elevated"
}
"""
    question = {
    "content": topic["stem"]["content"],
    "remark": topic["stem"]["remark"],
    "word_len": topic["w_len"],
    "word_tip": topic["w_tip"]
    }
    options = topic["options"]
    answer = deepseek_api.get_answer(system_prompt, str(question))
    return answer