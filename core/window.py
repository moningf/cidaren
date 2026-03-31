import pymem
import time

PROCESS_NAME = "WeChatAppEx.exe"
TARGET = "UserToken:"

def window_get_token():
    try:
        pm = pymem.Pymem(PROCESS_NAME)
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