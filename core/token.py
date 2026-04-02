import pymem
import time
import psutil

PROCESS_NAME = "WeChatAppEx.exe"
TARGET = "UserToken:"

def get_pids(process_name=PROCESS_NAME)->list:
    """通过进程名称获取PID"""
    list = []
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if proc.info['name'] == process_name:
            list.append(proc.info['pid'])
    return list

def window_get_token():
    pid = get_pids()[-1]
    try:
        pm = pymem.Pymem(pid)
        addresses = pm.pattern_scan_all(TARGET.encode('utf-8'),return_multiple=False)
        data = pm.read_bytes(addresses, 100).decode('utf-8')
        token = data.replace(":", "").split()[1]
    except Exception as e:
        print("Retrying in 10 seconds...")
        time.sleep(10)
        token = window_get_token()
    return token

if __name__ == "__main__":
    token = window_get_token()
    print(f"Token: {token}")
