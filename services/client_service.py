from core.client import HttpClient
from api import class_task_api
from core.decoder import find_noise_positions,decode
base_url = "https://app.vocabgo.com/student/api"

class ClientService:
    def __init__(self, token=None):
        self.client = HttpClient(base_url, token=token)
        self.tasks_list = []
        self.task_info = {}
        if token:
            self.warmup_cache()
        
    def warmup_cache(self):
        """按需预热缓存"""
        self.get_tasks_list()
        # for task in self.tasks_list:
        #     task_info1 = self.get_task_info(task["task_id"])

    def set_token(self, token):
        """设置Token并预热缓存"""
        self.client.set_token(token)
        self.warmup_cache()

    def get_tasks_list(self)-> list:
        """获取任务列表"""
        if self.tasks_list is not None and len(self.tasks_list) > 0:
            return self.tasks_list
        self.tasks_list = class_task_api.page_task(self.client)["data"]["records"]
        return self.tasks_list

    def get_task_info(self, task_id) -> dict:
        """获取任务详情"""
        if task_id in self.task_info.keys():
            return self.task_info[task_id]
        self.task_info[task_id] = class_task_api.get_task_info(self.client, task_id)["data"]
        return self.task_info[task_id]
    def chose_word_list(self, task_id):
        """选择单词列表展示（尽量使用获取任务详情接口）"""
        result = class_task_api.chose_word_list(self.client, task_id)["data"]
        return result
    def submit_chose_word(self, task_id, word_map):
        """提交选词"""
        result = class_task_api.submit_chose_word(self.client, task_id, word_map)
        return result
    def start_answer(self, task_id, task_type, release_id):
        """获取题目内容"""
        result = class_task_api.start_answer(self.client, task_id, task_type, release_id)["data"]
        result = decode(result)
        return result
    def submit_answer_and_save(self, topic_code, answer=None, app_type=1):
        """提交答案"""
        result = class_task_api.submit_answer_and_save(self.client, topic_code, answer, app_type)["data"]
        result = decode(result)
        return result
    def verify_answer(self, topic_code, answer, app_type=1):
        """验证答案"""
        result = class_task_api.verify_answer(self.client, topic_code, answer, app_type)["data"]
        result = decode(result)
        return result
    def study_word(self, task_id, word):
        """学习单词"""
        word_list_info = self.get_task_info(task_id)
        course_id = word_list_info["course_id"]
        list_id = word_list_info["word_list"][0]["list_id"]
        result = class_task_api.study_word(self.client, course_id, list_id, word)["data"]
        result = decode(result)
        return result