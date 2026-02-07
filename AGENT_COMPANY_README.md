# MetaGPT Agent Company

AI驱动的虚拟软件公司，实现9阶段软件开发流程自动化。

## 项目概述

本项目实现了一个由AI角色组成的虚拟软件公司，模拟真实的软件开发团队协作流程。通过群聊讨论的方式，8个AI角色（老板、产品经理、架构师、产品设计师、项目经理、开发工程师、测试工程师、运维工程师）协同工作，完成从需求分析到运维监控的完整软件开发生命周期。

## 9阶段开发流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1.需求分析  │ -> │ 2.技术方案  │ -> │ 3.UI/UX设计 │
│  (产品经理)  │    │  (架构师)   │    │ (产品设计师) │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
┌─────────────┐    ┌─────────────┐    ┌─────┴───────┐
│  4.任务拆解  │ <- │ 5.编码实现  │ <- │  6.UI验收   │
│  (项目经理)  │    │ (开发工程师) │    │ (产品设计师) │
└─────────────┘    └─────────────┘    └─────────────┘
       │
       v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  7.功能测试  │ -> │ 8.部署上线  │ -> │ 9.运维监控  │
│ (测试工程师) │    │  (项目经理)  │    │ (运维工程师) │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 阶段详情

| 阶段 | 名称 | 负责人 | 输出物 |
|------|------|--------|--------|
| P1 | 需求分析 | 产品经理 | PRD文档 |
| P2 | 技术方案设计 | 架构师 | 架构设计文档 |
| P3 | UI/UX设计 | 产品设计师 | 设计稿 |
| P4 | 任务拆解 | 项目经理 | 任务清单 |
| P5 | 编码实现 | 开发工程师 | 可运行代码 |
| P6 | UI验收 | 产品设计师 | 验收报告 |
| P7 | 功能测试 | 测试工程师 | 测试报告 |
| P8 | 部署上线 | 项目经理 | 部署文档 |
| P9 | 运维监控 | 运维工程师 | 监控方案 |

## 项目结构

```
/mnt/okcomputer/output/
├── main.py                    # 主程序入口
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖列表
├── README.md                 # 项目说明
│
├── architecture/             # 架构模块
│   ├── base.py              # 基础类和枚举
│   ├── role.py              # 角色基类和实现
│   ├── phase.py             # 阶段管理
│   ├── message.py           # 消息系统
│   ├── discussion_engine.py # 讨论引擎
│   ├── consensus.py         # 共识检测
│   └── turn_manager.py      # 轮流管理
│
├── roles/                    # 角色模块
│   ├── role_matrix.py       # 角色职责矩阵
│   ├── product_manager.py   # 产品经理
│   ├── architect.py         # 架构师
│   ├── product_designer.py  # 产品设计师
│   ├── project_manager.py   # 项目经理
│   ├── engineer.py          # 开发工程师
│   ├── qa_engineer.py       # 测试工程师
│   ├── devops.py            # 运维工程师
│   └── boss.py              # 老板
│
├── discussion/               # 讨论引擎模块
│   ├── engine.py            # 核心引擎
│   ├── message.py           # 消息处理
│   ├── state.py             # 状态管理
│   ├── consensus.py         # 共识算法
│   └── round_robin.py       # 轮流机制
│
├── feishu/                   # 飞书机器人模块
│   ├── bot.py               # 机器人主类
│   ├── message.py           # 消息处理
│   ├── group.py             # 群聊管理
│   ├── card.py              # 卡片消息
│   └── reminder.py          # 提醒功能
│
└── company/                  # 公司主模块
    ├── __init__.py
    ├── agent_company.py     # 公司主类
    └── workflow.py          # 工作流管理
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml` 文件，设置：
- LLM API密钥（智谱GLM-4）
- 飞书应用凭证（可选）

### 3. 运行

```bash
# 交互模式
python main.py

# 运行演示项目
python main.py --demo

# 启动指定项目
python main.py --idea "开发一个待办事项应用"

# 运行单个阶段
python main.py --phase P1 --idea "开发一个待办事项应用"

# 启动Web服务器
python main.py --web --port 8000
```

## 使用示例

### 交互模式

```bash
$ python main.py

============================================================
MetaGPT Agent Company - 交互模式
============================================================
命令:
  start <idea>  - 启动新项目
  status        - 查看当前状态
  phases        - 查看阶段列表
  roles         - 查看角色列表
  stop          - 停止当前项目
  quit          - 退出
============================================================

AgentCompany> start 开发一个简单的博客系统
```

### API接口

启动Web服务器后，可使用以下API：

```bash
# 查看状态
curl http://localhost:8000/status

# 查看角色列表
curl http://localhost:8000/roles

# 查看阶段列表
curl http://localhost:8000/phases

# 创建新项目
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"idea": "开发一个待办事项应用", "name": "TodoApp"}'
```

## 核心特性

### 1. 群聊讨论机制
- 狼人杀式轮流发言
- 每阶段最多20轮讨论
- 自动检测达成共识

### 2. 共识检测算法
- 显式同意检测
- 内容相似度分析
- LLM智能判断
- 混合策略

### 3. 老板介入机制
- 任意消息触发检测
- 关键词识别
- 强制决策能力

### 4. 飞书集成
- 实时消息推送
- 群聊讨论展示
- 卡片消息支持

### 5. 状态持久化
- 自动保存讨论状态
- 支持断点续传
- 结果导出

## 配置说明

### config.yaml

```yaml
# LLM配置
llm:
  api_key: "your-api-key"
  model: "glm-4"
  base_url: "https://open.bigmodel.cn/api/paas/v4"

# 飞书配置
feishu:
  app_id: "your-app-id"
  app_secret: "your-app-secret"

# 讨论引擎配置
discussion:
  max_rounds_per_phase: 20
  consensus_threshold: 0.8
```

## 角色职责矩阵（RACI）

| 角色 | P1需求 | P2架构 | P3设计 | P4任务 | P5编码 | P6验收 | P7测试 | P8部署 | P9运维 |
|------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| 老板 | A | A | A | A | C | A | A | A | A |
| 产品经理 | A | C | R | C | I | R | C | I | I |
| 架构师 | R | A | I | C | R | I | I | C | C |
| 产品设计师 | C | I | A | I | I | A | I | I | I |
| 项目经理 | I | I | I | A | C | I | C | A | I |
| 开发工程师 | I | R | I | R | A | R | R | R | R |
| 测试工程师 | I | I | I | R | I | C | A | I | I |
| 运维工程师 | I | C | I | I | I | I | I | R | A |

*A=Accountable(最终负责), R=Responsible(执行), C=Consulted(咨询), I=Informed(知情)*

## 开发计划

- [x] 基础架构设计
- [x] 角色系统实现
- [x] 9阶段流程定义
- [x] 讨论引擎开发
- [x] 共识检测算法
- [x] 飞书机器人集成
- [x] 状态持久化
- [ ] LLM接入完善
- [ ] 实际代码生成
- [ ] 更多测试用例

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交Issue或Pull Request。
