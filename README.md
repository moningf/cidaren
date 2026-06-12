# Cidaren — 词达人自动答题

VocabGo（词达人）微信小程序英语练习自动答题工具。通过提取微信进程中的认证 Token，驱动状态机自动完成班级任务和自学任务。

## 功能

- **Web 任务面板** — 浅色主题的本地 Web 界面，查看、选择、执行任务
- **Token 自动获取** — 从微信进程内存中提取 UserToken（Windows / Linux）
- **多题型支持** — 支持 6 种题型（mode 0/11/22/31/32/51）
- **AI 兜底** — 词表匹配失败时，通过 AI（兼容 OpenAI API）兜底作答
- **响应解密** — 自动识别并解密 VocabGo 的 jv 混淆响应（v1/v2/v3）
- **自学任务** — 支持自定义课程和难度等级的自学模式

## 快速开始

### 环境要求

- Python 3.11+
- 微信客户端（需登录并打开词达人小程序）

### 方式一：uv

```bash
git clone https://github.com/yourusername/cidaren.git
cd cidaren
uv sync
uv run python main.py
```

### 方式二：pip

```bash
git clone https://github.com/yourusername/cidaren.git
cd cidaren
pip install -r requirements.txt
python main.py
```

打开浏览器访问 `http://127.0.0.1:8741`。Token 和 AI 配置通过 Web 界面右上角 ⚙ 设置按钮完成。

## 使用说明

1. 确保微信已登录并打开词达人小程序
2. 启动 Cidaren，打开浏览器面板
3. 面板会自动尝试从微信进程获取 Token
4. 获取成功后自动加载「班级任务」列表
5. 勾选需要的任务，点击「开始选中任务」
6. 实时查看答题日志和进度

## 免责声明

本项目仅供学习和研究使用。使用者应自行承担因使用本项目产生的一切责任。请遵守相关平台的服务条款。

## License

MIT License — 详见 [LICENSE](LICENSE)
