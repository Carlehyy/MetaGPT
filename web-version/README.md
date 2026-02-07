# AI虚拟软件公司 - Web版

## 项目简介

AI驱动的虚拟软件公司Web可视化平台，8个AI角色按照职责矩阵协作完成软件开发全流程。

### 核心特性

- **8个AI角色**: 老板、产品经理、架构师、产品设计师、项目经理、开发工程师、测试工程师、运维工程师
- **9阶段流程**: 需求分析 → 技术方案 → UI设计 → 任务拆解 → 编码实现 → UI验收 → 功能测试 → 部署上线 → 运维监控
- **Web可视化**: 极简美观的聊天界面，实时展示团队协作
- **@提醒功能**: AI需要咨询老板时自动@提醒，支持多次提醒
- **职责矩阵**: 严格按照预设规则执行各阶段任务

## GitHub地址

**分支**: `agent-company`
**地址**: https://github.com/Carlehyy/MetaGPT/tree/agent-company/web-version

## 快速开始

### 1. 克隆代码

```bash
git clone -b agent-company https://github.com/Carlehyy/MetaGPT.git
cd MetaGPT/web-version
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`，设置智谱GLM-4 API密钥:

```yaml
llm:
  api_key: "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
```

### 3. 启动服务

```bash
python main.py --port 8000
```

### 4. 访问

- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs

## 项目文档

- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目完整总结
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 详细部署指南
- [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md) - GitHub上传说明
- [PROJECT_README.md](PROJECT_README.md) - 项目详细说明

## 项目结构

```
/mnt/okcomputer/output/
├── main.py                 # 主入口
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖列表
├── start.sh               # 启动脚本
├── web-version.tar.gz     # 完整压缩包
│
├── backend/               # 后端模块 (FastAPI)
├── roles/                 # 角色系统 (8个AI角色)
├── discussion/            # 讨论引擎
├── company/               # 公司主类
├── templates/             # 前端模板
└── static/                # 静态资源
```

## 技术栈

- **后端**: Python 3.9+, FastAPI, WebSocket
- **前端**: HTML5, Tailwind CSS, JavaScript
- **AI**: 智谱GLM-4

## 代码统计

- **总代码行数**: 8,086+ 行
- **Python代码**: 6,228 行
- **前端代码**: 1,281 行
- **文件数量**: 33 个

## 许可证

MIT License

---

**项目状态**: ✅ 已完成
**完成日期**: 2026-02-08
