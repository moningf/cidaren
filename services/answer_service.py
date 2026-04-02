from services.client_service import ClientService
class Answer_Unit:
    def __init__(self, client_service:ClientService):
        self.client_service = client_service
        self.choose_task()

    def choose_task(self):
        """选择班级任务"""
        for i in range(len(self.client_service.tasks_list)):
            print(f"{i}: {self.client_service.tasks_list[i]['task_name']}")
        choice = int(input("请选择任务: "))
        task = self.client_service.tasks_list[choice]
        self.release_id = task["release_id"]
        self.task_type = task["task_type"]
        self.task_id = task["task_id"]
        self.task_name = task["task_name"]

    def answer(self,topic):
        """提交答案"""
        if topic['task_type'] == 0:
            self.answer_00(topic)

    def start_answer(self):
        topic = self.client_service.start_answer(task_id=self.task_id, task_type=self.task_type, release_id=self.release_id)
        return topic

    def answer_00(self,topic):
        topic_code = topic["topic_code"]
        result = self.client_service.submit_answer_and_save(topic_code)
        return result