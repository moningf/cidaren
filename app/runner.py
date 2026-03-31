from services import auth_service
import time
from services.client_service import ClientService

def run():
    client_service = ClientService(auth_service.get_token())
    # print(client_service.get_task_info(client_service.tasks_list[0]["task_id"]))
    # for task in tasks:
    #     task_info = client_service.get_task_info(task["task_id"])
    #     print(task_info)
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
    # pos = client_service.find_noise_pos()
    # print(pos)
    # data = client_service.start_answer(task_id=client_service.tasks_list[0]["task_id"], task_type=client_service.tasks_list[0]["task_type"], release_id=client_service.tasks_list[0]["release_id"])
    # next_Topic = data["topic_code"]
    # print(data)
    # for i in range(5):
    # nex = client_service.submit_answer_and_save(topic_code=next_Topic, app_type=1)
    # print(nex)
    # next_Topic = nex["topic_code"]
if __name__ == "__main__":
    run()