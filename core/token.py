import pymem
import re
import time
import psutil

PROCESS_NAME = "WeChatAppEx.exe"
TARGET = "UserToken:"
# TARGET = "ABC:"

def get_pids(process_name=PROCESS_NAME)->list:
    """通过进程名称获取PID"""
    list = []
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if proc.info['name'] == process_name:
            list.append(proc.info['pid'])
    return list

def window_get_token():
    pid = get_pids()[1]
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

def linux_get_token(search_pattern=TARGET):
    pid = get_pids()[0]
    maps_path = f"/proc/{pid}/maps"
    mem_path = f"/proc/{pid}/mem"
    
    # 将搜索字符串转为字节码
    search_bytes = search_pattern.encode('utf-8')
    found_addresses = []

    try:
        with open(maps_path, 'r') as maps_file:
            for line in maps_file:
                # 解析 maps 每一行，获取地址范围和权限
                # 格式如: 55ca6334a000-55ca6334b000 r--p 00000000 ...
                res = re.match(r'([0-9a-f]+)-([0-9a-f]+)\s+([r-][w-][x-][p-])', line)
                if not res: continue
                
                start_addr = int(res.group(1), 16)
                end_addr = int(res.group(2), 16)
                permissions = res.group(3)

                # 只扫描可读 (r) 的内存区域，跳过不可读的
                if 'r' in permissions:
                    try:
                        with open(mem_path, 'rb') as mem_file:
                            mem_file.seek(start_addr)
                            chunk = mem_file.read(end_addr - start_addr)
                            
                            # 在当前块中搜索
                            index = chunk.find(search_bytes)
                            if index != -1:
                                actual_addr = start_addr + index
                                found_addresses.append(hex(actual_addr))
                                # 提取特征值后面的内容（假设是 Token 内容）
                                content = chunk[index:index+260].decode('utf-8', errors='ignore')
                                # print(f"找到特征！地址: {hex(actual_addr)} | 内容: {content}")
                                token = content.replace(":","").split()[1]
                                return token
                    except (PermissionError, OSError):
                        continue # 有些内核区域即使标记为 r 也可能无法读取
    except Exception as e:
        print(f"发生错误: {e}")
    return found_addresses

if __name__ == "__main__":
    token = linux_get_token()
    # token = window_get_token()
    print(f"Token: {token}")
