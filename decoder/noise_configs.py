"""v2/v3 噪音配置表 — 对应 JS app.js:3795-3863 模块 58368."""
from typing import Any, Dict, List

# v2 噪音表: { jv_key: [ {site, num}, ... ] }
# 按顺序删除：在 site 位置删除 num 个字符
V2_NOISE_CONFIGS: Dict[str, List[Dict[str, int]]] = {
    "2_1254": [
        {"site": 0, "num": 3},
        {"site": 1, "num": 2},
        {"site": 31, "num": 1},
        {"site": 41, "num": 2},
        {"site": 51, "num": 1},
        {"site": 87, "num": 1},
        {"site": 97, "num": 1},
    ],
    "2_10234": [
        {"site": 0, "num": 3},
        {"site": 1, "num": 4},
        {"site": 39, "num": 1},
        {"site": 57, "num": 2},
        {"site": 188, "num": 1},
        {"site": 259, "num": 1},
        {"site": 316, "num": 2},
    ],
    "2_9214": [
        {"site": 0, "num": 3},
        {"site": 1, "num": 4},
        {"site": 41, "num": 2},
        {"site": 57, "num": 1},
        {"site": 139, "num": 2},
        {"site": 272, "num": 1},
        {"site": 361, "num": 2},
    ],
    "2_9314": [
        {"site": 0, "num": 3},
        {"site": 1, "num": 4},
        {"site": 31, "num": 2},
        {"site": 60, "num": 1},
        {"site": 152, "num": 2},
        {"site": 256, "num": 1},
    ],
}

# v3 分块重排表: { jv_key: { updateChars, average, locations } }
V3_BLOCK_CONFIGS: Dict[str, Dict[str, Any]] = {
    "3_1021": {
        "updateChars": [
            {"site": 0, "num": 1},
            {"site": 1, "num": 2},
            {"site": 33, "num": 1},
            {"site": 57, "num": 1},
            {"site": 111, "num": 1},
        ],
        "average": 5,
        "locations": [1, 3, 2, 0, 4],
    },
    "3_2265": {
        "updateChars": [
            {"site": 0, "num": 2},
            {"site": 1, "num": 3},
            {"site": 33, "num": 1},
            {"site": 57, "num": 1},
            {"site": 121, "num": 1},
        ],
        "average": 5,
        "locations": [3, 1, 0, 4, 2],
    },
    "3_2277": {
        "updateChars": [
            {"site": 0, "num": 3},
            {"site": 1, "num": 3},
            {"site": 32, "num": 2},
            {"site": 50, "num": 1},
            {"site": 110, "num": 1},
        ],
        "average": 5,
        "locations": [3, 1, 0, 4, 2],
    },
}


def remove_noise_chars(s: str, noise_rules: List[Dict[str, int]]) -> str:
    """按噪音规则顺序删除字符（v2 和 v3 共用）."""
    result = s
    for rule in noise_rules:
        site = rule["site"]
        num = rule["num"]
        before = result[:site] if site > 0 else ""
        after = result[site + num:]
        result = before + after
    return result


def reorder_blocks(s: str, block_config: Dict[str, Any]) -> str:
    """分块重排算法 — 对应 v3 的 Step 2-4."""
    average = block_config["average"]
    locations = block_config["locations"]

    block_size = len(s) // average
    blocks = [s[j * block_size:(j + 1) * block_size] for j in range(average)]

    result_parts = [blocks[locations.index(k)] for k in range(average)]
    result = "".join(result_parts)

    remainder = len(s) % block_size
    if remainder > 0:
        result += s[average * block_size:]

    return result
