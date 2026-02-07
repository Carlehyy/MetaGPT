# AI虚拟软件公司 - 部署指南

## 项目完成总结

### 已完成的工作

#### 1. Web前端界面
- **文件**: `templates/index.html`, `static/css/style.css`, `static/js/app.js`
- **特性**:
  - 极简现代设计，支持深色/浅色主题
  - 左侧边栏显示9个开发阶段
  - 中间聊天区域显示角色对话
  - 右侧边栏显示团队成员
  - @老板消息特殊高亮
  - WebSocket实时通信

#### 2. 后端API服务
- **文件**: `backend/*.py`
- **特性**:
  - FastAPI框架
  - WebSocket支持
  - RESTful API
  - 消息存储
  - 提醒服务（@老板多次提醒）

#### 3. 角色系统
- **文件**: `roles/*.py`
- **特性**:
  - 8个AI角色完整实现
  - 职责矩阵逻辑
  - 智谱GLM-4集成
  - 角色轮流发言

#### 4. 讨论引擎
- **文件**: `discussion/*.py`
- **特性**:
  - 狼人杀式轮流发言
  - 共识检测算法
  - @老板逻辑
  - 阶段管理

### 项目结构

```
/mnt/okcomputer/output/
├── main.py                    # 主入口 (74行)
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖列表
├── start.sh                  # 启动脚本
├── PROJECT_README.md         # 项目说明
├── DEPLOYMENT_GUIDE.md       # 部署指南
│
├── backend/                  # 后端模块 (1568行)
│   ├── main.py              # FastAPI主应用
│   ├── api.py               # API路由 (506行)
│   ├── websocket.py         # WebSocket管理 (308行)
│   ├── storage.py           # 消息存储 (238行)
│   └── reminder.py          # 提醒服务 (294行)
│
├── roles/                    # 角色模块 (3361行)
│   ├── role_matrix.py       # 职责矩阵 (336行)
│   ├── base_role.py         # 角色基类 (413行)
│   ├── boss.py              # 老板 (160行)
│   ├── product_manager.py   # 产品经理 (388行)
│   ├── architect.py         # 架构师 (399行)
│   ├── product_designer.py # 产品设计师 (375行)
│   ├── project_manager.py   # 项目经理 (442行)
│   ├── engineer.py          # 开发工程师 (385行)
│   ├── qa_engineer.py       # 测试工程师 (466行)
│   └── devops.py            # 运维工程师 (423行)
│
├── discussion/               # 讨论引擎 (646行)
│   └── engine.py            # 讨论引擎主类 (619行)
│
├── company/                  # 公司模块 (653行)
│   └── agent_company.py     # 公司主类 (629行)
│
├── templates/                # 前端模板
│   └── index.html           # 主页面 (164行)
│
└── static/                   # 静态资源
    ├── css/style.css        # 样式 (483行)
    └── js/app.js            # JavaScript (634行)

总计: 8086+ 行代码
```

## 部署步骤

### 1. 环境准备

```bash
# 确保Python 3.9+已安装
python3 --version

# 安装依赖
cd /mnt/okcomputer/output
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`:

```yaml
llm:
  api_key: "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
  model: "glm-4"
  base_url: "https://open.bigmodel.cn/api/paas/v4"
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接启动
python main.py --port 8000
```

### 4. 访问

- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

## 上传到GitHub

由于本地git有问题，请手动上传文件:

1. 访问 https://github.com/Carlehyy/MetaGPT
2. 创建新分支 `agent-company-web`
3. 创建 `web-version/` 目录
4. 上传所有文件

或使用GitHub CLI:

```bash
# 安装gh
apt install gh

# 登录
gh auth login

# 创建分支并上传
gh repo fork Carlehyy/MetaGPT --clone=false
# 然后手动上传文件
```

## 验证清单

- [x] 后端API服务启动成功
- [x] WebSocket连接正常
- [x] 角色系统导入成功
- [x] 讨论引擎运行正常
- [x] 前端页面可访问
- [x] @老板提醒功能实现
- [x] 职责矩阵逻辑正确

## 已知问题

1. 本地git有I/O错误，无法直接push到GitHub
2. 需要使用GitHub Web界面或API手动上传

## 后续优化建议

1. 添加数据库持久化存储
2. 实现用户认证系统
3. 添加更多AI模型支持
4. 优化前端性能
5. 添加测试用例
