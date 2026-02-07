# AI虚拟软件公司 - Web版

## 项目概述

本项目是MetaGPT Agent Company的Web改造版本，将原有的飞书群聊方式替换为Web页面，实现AI团队的协作可视化。

### 核心特性

- **8个AI角色协作**：老板、产品经理、架构师、产品设计师、项目经理、开发工程师、测试工程师、运维工程师
- **9阶段开发流程**：需求分析 → 技术方案 → UI设计 → 任务拆解 → 编码实现 → UI验收 → 功能测试 → 部署上线 → 运维监控
- **Web可视化界面**：极简美观的聊天界面，实时展示团队协作过程
- **@老板提醒**：AI需要咨询老板时会@提醒，支持多次提醒
- **职责矩阵**：严格按照预设的职责矩阵执行各阶段任务

## 项目结构

```
/mnt/okcomputer/output/
├── main.py                    # 主入口
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖列表
├── start.sh                  # 启动脚本
│
├── backend/                  # 后端模块
│   ├── main.py              # FastAPI主应用
│   ├── api.py               # API路由
│   ├── websocket.py         # WebSocket管理
│   ├── storage.py           # 消息存储
│   └── reminder.py          # 提醒服务
│
├── roles/                    # 角色模块
│   ├── role_matrix.py       # 职责矩阵
│   ├── base_role.py         # 角色基类
│   ├── boss.py              # 老板
│   ├── product_manager.py   # 产品经理
│   ├── architect.py         # 架构师
│   ├── product_designer.py # 产品设计师
│   ├── project_manager.py   # 项目经理
│   ├── engineer.py          # 开发工程师
│   ├── qa_engineer.py       # 测试工程师
│   └── devops.py            # 运维工程师
│
├── discussion/               # 讨论引擎
│   └── engine.py            # 讨论引擎主类
│
├── company/                  # 公司模块
│   └── agent_company.py     # 公司主类
│
├── templates/                # 前端模板
│   └── index.html           # 主页面
│
└── static/                   # 静态资源
    ├── css/style.css        # 样式文件
    └── js/app.js            # JavaScript
```

## 快速开始

### 1. 安装依赖

```bash
cd /mnt/okcomputer/output
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml` 文件，配置智谱GLM-4 API密钥：

```yaml
llm:
  api_key: "your-api-key"
```

### 3. 启动服务

```bash
# 方式1：使用启动脚本
./start.sh

# 方式2：直接启动
python main.py --port 8000
```

### 4. 访问Web界面

- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

## API接口

### REST API

- `GET /api/phases` - 获取所有阶段信息
- `GET /api/phase/current` - 获取当前阶段
- `GET /api/messages` - 获取历史消息
- `POST /api/idea` - 提交新需求
- `GET /api/roles` - 获取所有角色信息
- `GET /api/status` - 获取系统状态
- `POST /api/messages/send` - 发送消息
- `POST /api/boss/reply` - 老板回复

### WebSocket

- `ws://localhost:8000/ws` - 普通客户端连接
- `ws://localhost:8000/ws/boss` - 老板专用连接

## 职责矩阵

| 阶段 | 老板 | 产品经理 | 架构师 | 设计师 | 项目经理 | 开发 | 测试 | 运维 |
|------|------|----------|--------|--------|----------|------|------|------|
| P1需求分析 | 咨询 | **负责** | 知会 | 知会 | 知会 | - | - | - |
| P2技术方案 | 咨询 | 咨询 | **负责** | - | 知会 | 咨询 | 知会 | 咨询 |
| P3UI设计 | 知会 | 验收 | - | **负责** | 知会 | 咨询 | - | - |
| P4任务拆解 | - | 咨询 | 负责 | 知会 | **负责** | 咨询 | 咨询 | 咨询 |
| P5编码实现 | - | 知会 | 咨询 | - | 咨询 | **负责** | - | - |
| P6UI验收 | - | 验收 | - | **负责** | 知会 | 执行 | - | - |
| P7功能测试 | - | 验收 | 咨询 | 知会 | 咨询 | 执行 | **负责** | - |
| P8部署上线 | 验收 | 知会 | 咨询 | - | **负责** | 咨询 | 咨询 | 执行 |
| P9运维监控 | 知会 | 知会 | 咨询 | - | - | 咨询 | 知会 | **负责** |

## 技术栈

- **后端**: FastAPI, WebSocket, Python 3.9+
- **前端**: HTML5, Tailwind CSS, JavaScript
- **AI**: 智谱GLM-4

## 智谱GLM-4配置

```python
api_key = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
base_url = "https://open.bigmodel.cn/api/paas/v4"
model = "glm-4"
```

## 开发说明

### 添加新角色

1. 在 `roles/` 目录下创建新角色文件
2. 继承 `BaseRole` 基类
3. 实现 `get_system_prompt()` 方法
4. 在 `roles/__init__.py` 中导出

### 修改职责矩阵

编辑 `roles/role_matrix.py` 文件，修改 `ROLE_PHASE_MATRIX` 字典。

### 自定义提醒规则

编辑 `backend/reminder.py` 文件，修改 `ReminderConfig` 配置。

## 许可证

MIT License
