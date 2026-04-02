from services import auth_service
from services.answer_service import Answer_Unit
import time
from services.client_service import ClientService

def run():
    client_service = ClientService(auth_service.get_token())
    # print(auth_service.get_token())
    # print(client_service.get_task_info(client_service.tasks_list[0]["task_id"]))
    # tasks = client_service.get_tasks_list()
    # for task in tasks:
    #     task_info = client_service.get_task_info(task["task_id"])
    unit = Answer_Unit(client_service)
    topic = unit.start_answer()
    while(topic is not None):
        topic = unit.answer(topic)

    ##提交选择单词
    # word_list_info = client_service.chose_word_list(tasks[0]["task_id"])
    # word_list = word_list_info["word_list"]
    # # print(word_list)
    # key = word_list_info["course_id"] + ":" + word_list_info["word_list"][0]["list_id"]
    # print(key)
    # value  = []
    # for word in word_list:
    #     if word["score"] != 10:
    #         value.append(word["word"])
    # map = {}
    # map[key]=value
    # result = client_service.submit_chose_word(tasks[0]["task_id"], map)
    # print(result)

    ## 答题
    # data = client_service.start_answer(task_id=client_service.tasks_list[0]["task_id"], task_type=client_service.tasks_list[0]["task_type"], release_id=client_service.tasks_list[0]["release_id"])
    # next_Topic = data["topic_code"]
    # print(data)
    # ans = 1
    # while ans:
    #     result = client_service.submit_answer_and_save(topic_code=next_Topic, app_type=1)
    #     print(result)
    #     next_Topic = result["topic_code"]
    #     ans = input()
        
    # nex = client_service.submit_answer_and_save(topic_code=next_Topic, app_type=1)
    # print(nex)
    # next_Topic = nex["topic_code"]
if __name__ == "__main__":
    run()