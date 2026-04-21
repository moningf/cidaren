import json
from openai import OpenAI

client = OpenAI(
    api_key="sk-59b7f790996c4910baf93ee19705ab78",
    base_url="https://api.deepseek.com",
)

def get_answer(system_prompt, user_prompt):
    messages:list = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    temperature=0,
    response_format={
        'type': 'json_object'
    }
    )
    return json.loads(response.choices[0].message.content or "{}")

if __name__ == "__main__":
    system_prompt = """
请根据以下每道题的题目内容，从选项中选择正确的英文单词对应的序号，返回 JSON 数组。
注意:   1. 每个'_'为一个选项（重要!!！不可少选，不可多选）
        2. 选项下标从0开始。
Example:
{"content":"_ _","remark": "职业展望","options": ["envy","outlook","career","rage"]}

Answer:
{
answer: [2,1]
}
"""
    user_prompt = """
{"content": "_..._ _", "remark": "把......强加给某人"，"options":["sb.","on","enforce","acid"]}
"""
    res = get_answer(system_prompt, user_prompt)
    print(res)