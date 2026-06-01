# 🧮 LeetCode 进度追踪器

一个基于 Flask 的 LeetCode 刷题进度管理 Web 应用，内置 40 道高频面试题、算法套路地图、30天刷题计划、代码模板库，以及 AI 智能分析功能。

## ✨ 主要功能

- **仪表盘** — 总览完成进度、难度分布、连续打卡天数 (streak)、热力图、分类掌握度、智能推荐下一题
- **题目列表** — 40 道精选高频题（P0/P1/P2 优先级），支持按难度、分类、状态、书签筛选
- **套路地图** — 13 大算法分类的触发条件、数据结构、记忆口诀一览
- **30天计划** — 4 周分阶段刷题计划，自动追踪每周进度
- **模板库** — 各分类的经典解题模板代码
- **AI 分析** — 调用 LLM API 分析题目思路、复杂度、代码审查，支持生成每周刷题报告
- **题目标记** — 支持 todo / in_progress / done / review 四种状态切换，以及书签、笔记功能

## 🛠 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3 + Flask |
| 数据库 | SQLite |
| 前端 | Jinja2 模板 + Chart.js + 霞鹜文楷字体 |
| AI 模块 | OpenAI 兼容 API (默认 mimo-v2.5-pro) |
| 部署 | systemd 服务 |

## 📁 项目结构

```
leetcode-tracker/
├── app.py              # Flask 主应用（路由、API）
├── database.py         # 数据库模型、种子数据、统计查询
├── ai_analysis.py      # AI 分析模块（题目分析 + 周报生成）
├── leetcode.db         # SQLite 数据库文件
├── .gitignore
├── static/
│   ├── css/
│   │   └── style.css   # 主样式表
│   └── style.css
└── templates/
    ├── base.html           # 基础布局模板
    ├── index.html          # 仪表盘页面
    ├── problems.html       # 题目列表页面
    ├── problem_detail.html # 题目详情页面
    ├── roadmap.html        # 套路地图页面
    ├── plan.html           # 30天计划页面
    ├── templates.html      # 模板库页面
    └── analytics.html      # 数据分析页面
```

## 🚀 安装与运行

### 1. 克隆项目

```bash
git clone <repository-url> leetcode-tracker
cd leetcode-tracker
```

### 2. 安装依赖

```bash
pip install flask requests
```

### 3. 配置环境变量

创建 `.env` 文件或直接 export：

```bash
export LLM_API_KEY="your-api-key"          # LLM API 密钥（必填，否则 AI 功能不可用）
export LLM_API_BASE="https://api.example.com/v1"  # API 基础地址（可选，默认小米 mimo）
export LLM_MODEL="mimo-v2.5-pro"           # 模型名称（可选，默认 mimo-v2.5-pro）
```

同时需要在 `app.py` 中修改 HTTP Basic Auth 的用户名和密码：

```python
AUTH_USER = 'your-username'
AUTH_PASS = 'your-password'
```

### 4. 运行

```bash
python app.py
```

首次运行会自动初始化数据库并导入 40 道种子题目。服务默认监听 `0.0.0.0:8081`。

### 5. systemd 部署（可选）

创建 `/etc/systemd/system/leetcode-tracker.service`：

```ini
[Unit]
Description=LeetCode Progress Tracker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/leetcode-tracker
ExecStart=/usr/bin/python3 /root/leetcode-tracker/app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=LLM_API_KEY=your-api-key
Environment=LLM_API_BASE=https://api.example.com/v1
Environment=LLM_MODEL=your-model

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now leetcode-tracker
```

## 🔧 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | 空（AI 功能不可用） |
| `LLM_API_BASE` | OpenAI 兼容 API 地址 | `https://token-plan-sgp.xiaomimimo.com/v1` |
| `LLM_MODEL` | 模型名称 | `mimo-v2.5-pro` |

## 📡 API 接口

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/update_status` | POST | 更新题目状态 |
| `/api/update_notes` | POST | 更新笔记 |
| `/api/toggle_bookmark` | POST | 切换书签 |
| `/api/ai_analyze` | POST | AI 分析题目 |
| `/api/weekly_report` | GET | 生成周报 |
| `/api/heatmap` | GET | 热力图数据 |
| `/api/mastery` | GET | 分类掌握度 |
| `/api/recommendations` | GET | 智能推荐 |
| `/api/prediction` | GET | 完成预测 |
