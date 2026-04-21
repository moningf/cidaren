import os
from core.token import window_get_token
from core.token import linux_get_token

# 认证服务，负责获取用户Token并应用到HttpClient中
def get_token():
    if os.name == "nt":  # Windows
        token = window_get_token()
        return token
    elif os.name == 'posix':
        token = linux_get_token()
        print(f"Linux系统，获取到Token: {token}")
        return token
    else:
        # raise NotImplementedError("Token retrieval not implemented for this OS")
        print("非Windows系统，无法获取Token，请手动输入")
        token = input("请输入Token: ")
        return token


if __name__ == "__main__":
    # print(os.name)
    token = get_token()
    print(f"Token: {token}")
