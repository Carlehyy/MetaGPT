# GitHub上传指南

## 项目文件清单

由于网络环境限制，无法直接推送到GitHub，请按以下步骤手动上传。

### 准备文件

所有文件已打包: `/tmp/web-version.tar.gz` (147KB)

### 上传步骤

#### 方法1: 使用GitHub网页界面上传

1. 访问 https://github.com/Carlehyy/MetaGPT
2. 点击 "Add file" → "Upload files"
3. 选择分支: `agent-company-web` (如不存在则创建)
4. 创建目录 `web-version/`
5. 上传所有文件到该目录

#### 方法2: 使用GitHub Desktop

1. 克隆仓库到本地
2. 切换到 `agent-company-web` 分支
3. 创建 `web-version/` 目录
4. 复制所有文件到该目录
5. 提交并推送

#### 方法3: 使用Git命令行

```bash
# 克隆仓库
git clone -b agent-company-web https://github.com/Carlehyy/MetaGPT.git
cd MetaGPT

# 创建目录
mkdir -p web-version

# 复制文件（从服务器下载到本地后）
cp -r /path/to/output/* web-version/

# 提交
git add web-version/
git commit -m "Add Web version of AI Agent Company"
git push origin agent-company-web
```

### 文件结构

上传时请保持以下目录结构:

```
web-version/
├── main.py                    # 主入口
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖
├── start.sh                  # 启动脚本
├── PROJECT_README.md         # 项目说明
├── DEPLOYMENT_GUIDE.md       # 部署指南
├── GITHUB_UPLOAD_GUIDE.md    # 本文件
├── backend/                  # 后端模块
│   ├── __init__.py
│   ├── main.py
│   ├── api.py
│   ├── websocket.py
│   ├── storage.py
│   └── reminder.py
├── roles/                    # 角色模块
│   ├── __init__.py
│   ├── role_matrix.py
│   ├── base_role.py
│   ├── boss.py
│   ├── product_manager.py
│   ├── architect.py
│   ├── product_designer.py
│   ├── project_manager.py
│   ├── engineer.py
│   ├── qa_engineer.py
│   └── devops.py
├── discussion/               # 讨论引擎
│   ├── __init__.py
│   └── engine.py
├── company/                  # 公司模块
│   ├── __init__.py
│   └── agent_company.py
├── templates/                # 前端模板
│   └── index.html
└── static/                   # 静态资源
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

### 关键文件说明

#### 核心文件 (必须上传)
- `main.py` - 程序入口
- `config.yaml` - 配置文件（包含智谱GLM-4 API密钥）
- `requirements.txt` - Python依赖
- `start.sh` - 启动脚本

#### 后端模块
- `backend/main.py` - FastAPI主应用
- `backend/api.py` - RESTful API路由
- `backend/websocket.py` - WebSocket管理
- `backend/storage.py` - 消息存储
- `backend/reminder.py` - @老板提醒服务

#### 角色系统
- `roles/role_matrix.py` - 职责矩阵定义
- `roles/base_role.py` - 角色基类
- `roles/boss.py` - 老板角色
- `roles/product_manager.py` - 产品经理
- `roles/architect.py` - 架构师
- `roles/product_designer.py` - 产品设计师
- `roles/project_manager.py` - 项目经理
- `roles/engineer.py` - 开发工程师
- `roles/qa_engineer.py` - 测试工程师
- `roles/devops.py` - 运维工程师

#### 前端文件
- `templates/index.html` - 主页面
- `static/css/style.css` - 样式表
- `static/js/app.js` - JavaScript逻辑

### 验证上传

上传完成后，请验证:

1. 访问 https://github.com/Carlehyy/MetaGPT/tree/agent-company-web/web-version
2. 确认所有文件都已上传
3. 确认目录结构正确

### 启动测试

上传后，可以在服务器上测试:

```bash
# 拉取最新代码
git pull origin agent-company-web

# 进入目录
cd web-version

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py --port 8000
```

### 访问地址

- Web界面: http://38.14.254.160:8000
- API文档: http://38.14.254.160:8000/docs

### 技术支持

如有问题，请检查:
1. 文件是否完整上传
2. 目录结构是否正确
3. 依赖是否安装成功
4. 端口是否开放
