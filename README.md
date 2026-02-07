# AI Team - 智能软件开发团队

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/AI-Team-orange" alt="AI Team">
</p>

**AI Team** 是一个由8个AI角色组成的虚拟软件公司，通过群聊讨论协作完成从需求分析到运维监控的完整软件开发生命周期。

🚀 **9阶段软件开发流程自动化** | 💬 **狼人杀式群聊讨论** | 🤖 **飞书机器人集成**

---

## 📢 最新动态

**2026-02-07** 🎉 AI Team v1.0 正式发布！支持9阶段软件开发流程、群聊讨论模式、飞书机器人集成。

---

## ✨ 核心特性

### 🏢 8个AI角色协同工作

| 角色 | 职责 | 负责阶段 |
|------|------|----------|
| 👔 **老板** | 战略决策、最终审批 | 关键决策点 |
| 📋 **产品经理** | 需求分析、产品规划 | P1 需求分析 |
| 🏗️ **架构师** | 技术方案、架构设计 | P2 技术方案设计 |
| 🎨 **产品设计师** | UI/UX设计、设计验收 | P3 UI/UX设计、P6 UI验收 |
| 📊 **项目经理** | 项目管理、进度把控 | P4 任务拆解、P8 部署上线 |
| 💻 **开发工程师** | 编码实现、技术文档 | P5 编码实现 |
| 🧪 **测试工程师** | 功能测试、质量保障 | P7 功能测试 |
| 🚀 **运维工程师** | 运维监控、性能优化 | P9 运维监控 |

### 📋 9阶段软件开发流程

```
P1: 需求分析 → P2: 技术方案设计 → P3: UI/UX设计 → P4: 任务拆解
   → P5: 编码实现 → P6: UI验收 → P7: 功能测试 → P8: 部署上线 → P9: 运维监控
```

### 💬 群聊讨论模式

- **轮流发言**：狼人杀式轮询，确保每个角色有序发言
- **达成共识**：多策略共识检测（显式同意、Pass比例、内容相似度）
- **轮次限制**：每阶段最多20轮，防止无限讨论
- **老板介入**：随时@老板进行人工决策

### 🤖 飞书机器人集成

- 富文本卡片消息（角色头像、发言内容、当前轮数）
- 5分钟间隔提醒机制
- @提醒功能
- 分阶段群聊管理

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Team                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   讨论引擎   │  │   工作流    │  │  飞书机器人  │         │
│  │  Discussion │  │  Workflow   │  │   Feishu    │         │
│  │   Engine    │  │   Manager   │  │    Bot      │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │
│  ┌──────┴────────────────┴────────────────┴──────┐         │
│  │              AgentCompany 主类                │         │
│  └──────────────────┬────────────────────────────┘         │
│                     │                                       │
│  ┌──────────────────┴────────────────────────────┐         │
│  │              8个AI角色团队                     │         │
│  │  老板、产品经理、架构师、设计师、项目经理、    │         │
│  │  开发工程师、测试工程师、运维工程师           │         │
│  └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install httpx pyyaml pydantic
```

### 2. 配置API密钥

编辑 `config.yaml`：

```yaml
llm:
  api_key: "your_zhipu_api_key"
  model: "glm-4"

feishu:
  app_id: "your_feishu_app_id"
  app_secret: "your_feishu_app_secret"
```

### 3. 运行演示

```bash
python main.py --demo
```

### 4. 启动项目

```bash
python main.py --idea "开发一个智能客服系统"
```

---

## 📖 使用指南

### 飞书机器人配置

1. 在[飞书开放平台](https://open.feishu.cn/)创建企业自建应用
2. 获取 App ID 和 App Secret
3. 配置机器人权限：`im:chat:readonly`, `im:message:send`, `im:message:group_msg`
4. 将机器人添加到群聊

### 与AI团队协作

1. **@机器人** 并描述你的需求
2. **等待讨论** - AI团队会自动进行群聊讨论
3. **查看进度** - 通过飞书卡片查看讨论过程和决策
4. **介入决策** - 随时@老板进行人工干预

---

## 📁 项目结构

```
.
├── main.py                      # 主程序入口
├── config.yaml                  # 配置文件
├── requirements.txt             # 依赖列表
├── README.md                    # 项目说明
├── company/                     # 公司模块
│   ├── agent_company.py        # 公司主类
│   └── workflow.py             # 工作流管理
├── discussion/                  # 讨论引擎模块
│   ├── engine.py               # 讨论引擎核心
│   ├── consensus.py            # 共识检测
│   ├── state.py                # 状态管理
│   └── message.py              # 消息定义
├── feishu/                      # 飞书机器人模块
│   ├── bot.py                  # 机器人主类
│   ├── message.py              # 消息处理
│   ├── card.py                 # 卡片构建
│   └── reminder.py             # 提醒服务
└── roles/                       # 角色定义
    ├── role_matrix.py          # 职责矩阵
    ├── boss.py                 # 老板
    ├── product_manager.py      # 产品经理
    ├── architect.py            # 架构师
    ├── product_designer.py     # 产品设计师
    ├── project_manager.py      # 项目经理
    ├── engineer.py             # 开发工程师
    ├── qa_engineer.py          # 测试工程师
    └── devops.py               # 运维工程师
```

---

## ⚙️ 配置说明

### 讨论引擎配置

```yaml
discussion:
  max_rounds_per_phase: 20        # 每阶段最大轮数
  consensus_threshold: 0.8        # 共识阈值
  consensus_strategy: "HYBRID"    # 共识策略
  reminder_interval: 300          # 提醒间隔（秒）
```

### 共识检测策略

- **EXPLICIT**: 显式同意检测
- **PASS_RATIO**: Pass比例检测
- **CONTENT_SIMILARITY**: 内容相似度检测
- **HYBRID**: 混合策略（推荐）

---

## 🔧 高级功能

### 自定义角色

在 `roles/` 目录下创建新的角色类：

```python
from roles.role_matrix import ParticipationType

class MyRole(Role):
    def __init__(self):
        super().__init__(
            name="自定义角色",
            profile="角色描述",
            goal="角色目标",
            constraints="角色约束"
        )
```

### 自定义阶段

在 `company/workflow.py` 中添加新的阶段：

```python
PHASES = [
    {"id": "P10", "name": "自定义阶段", "leader": "产品经理"},
    # ...
]
```

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 💬 联系我们

- GitHub Issues: [提交问题](https://github.com/Carlehyy/MetaGPT/issues)
- 飞书群聊: 加入讨论

---

<p align="center">
  Made with ❤️ by AI Team
</p>
