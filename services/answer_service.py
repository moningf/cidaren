from services.client_service import ClientService
import time
class Answer_Unit:
    def __init__(self, client_service:ClientService):
        self.client_service = client_service
        self.choose_task()
        self.choose_word()

    def choose_task(self):
        """选择班级任务"""
        for i in range(len(self.client_service.tasks_list)):
            if self.client_service.tasks_list[i]["over_status"] == 2:
                # print(self.client_service.tasks_list[i])
                print(f"{i}: {self.client_service.tasks_list[i]['task_name']}")
                choice = int(input("请选择任务: "))
                task = self.client_service.tasks_list[choice]
                self.release_id = task["release_id"]
                self.task_type = task["task_type"]
                self.task_id = task["task_id"]
                self.task_name = task["task_name"]
    def choose_word(self):
        """选择单词"""
        word_list_info = self.client_service.chose_word_list(self.task_id)
        word_list = word_list_info["word_list"]
        key = word_list_info["course_id"] + ":" + word_list_info["word_list"][0]["list_id"]
        value  = []
        for word in word_list:
            if word["score"] != 10:
                value.append(word["word"])
        map = {}
        map[key]=value
        result = self.client_service.submit_chose_word(self.task_id, map)
        return result

    def answer(self,topic):
        """提交答案"""
        print(f"正在回答题目: {topic}")
        if topic['topic_mode'] == 0:     
            return self.answer_00(topic)
        if topic['topic_mode'] == 11:
            return self.answer_11(topic)

    def start_answer(self):
        topic = self.client_service.start_answer(task_id=self.task_id, task_type=self.task_type, release_id=self.release_id)
        return topic

    def answer_00(self,topic):
        time.sleep(1)
        topic_code = topic["topic_code"]
        result = self.client_service.submit_answer_and_save(topic_code)
        return result

    def answer_11(self,topic):
        time.sleep(2)
        topic_code = topic["topic_code"]
        answer = topic["answer_num"]
        result = self.client_service.verify_answer(topic_code,answer=answer)
        return result


