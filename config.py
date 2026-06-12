import json
from pathlib import Path

# 配置从 settings.json 加载，不在此文件硬编码敏感信息

USER_TOKEN = ""
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_settings_path = Path(__file__).parent / "settings.json"
if _settings_path.exists():
    try:
        _settings = json.loads(_settings_path.read_text())
        USER_TOKEN = _settings.get("user_token", USER_TOKEN)
        DEEPSEEK_API_KEY = _settings.get("deepseek_api_key", DEEPSEEK_API_KEY)
        DEEPSEEK_BASE_URL = _settings.get("deepseek_base_url", DEEPSEEK_BASE_URL)
    except Exception:
        pass
