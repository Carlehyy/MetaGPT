# 群聊讨论引擎模块

## 概述

本模块实现了一个完整的群聊讨论引擎，支持多智能体之间的协作讨论。主要功能包括：

1. **轮流发言机制** - 狼人杀式轮询，确保每个角色有序发言
2. **达成一致判断** - 多策略共识检测算法
3. **轮次限制控制** - 防止讨论无限进行
4. **老板介入检测** - 检测关键决策者介入
5. **讨论状态管理** - 完整的生命周期管理
6. **讨论消息存储** - 高效的消息管理和检索

## 架构设计

```
discussion/
├── __init__.py      # 模块导出
├── message.py       # 消息定义和存储
├── state.py         # 状态管理
├── round_robin.py   # 轮流发言管理
├── consensus.py     # 共识检测算法
├── engine.py        # 讨论引擎主类
└── README.md        # 本文档
```

## 核心概念

### 1. 讨论状态 (DiscussionState)

讨论可能处于以下状态：

- `PENDING` - 等待开始
- `ONGOING` - 进行中
- `CONSENSUS_REACHED` - 已达成一致
- `BOSS_NEEDED` - 需要老板决策
- `ROUNDS_EXHAUSTED` - 轮次耗尽
- `PAUSED` - 暂停
- `TERMINATED` - 已终止

### 2. 发言顺序策略 (TurnOrderStrategy)

- `FIXED` - 固定顺序
- `RANDOM` - 随机顺序
- `PRIORITY` - 优先级顺序
- `ROUND_ROBIN` - 轮询（循环）
- `REVERSE` - 反向顺序

### 3. 共识检测策略 (ConsensusStrategy)

- `KEYWORD_MATCH` - 关键词匹配
- `SIMILARITY` - 文本相似度
- `VOTING` - 投票统计
- `LLM_JUDGE` - LLM判断（预留）
- `HYBRID` - 混合策略（推荐）

## 使用示例

### 基础用法

```python
import asyncio
from discussion import (
    DiscussionEngine, Role, DiscussionConfig,
    DiscussionState, TurnOrderStrategy, ConsensusStrategy
)

async def main():
    # 1. 创建参与角色
    roles = [
        Role(id="pm", name="产品经理", description="负责产品规划", priority=1),
        Role(id="tech", name="技术负责人", description="负责技术方案", priority=2),
        Role(id="design", name="设计师", description="负责UI/UX", priority=3),
        Role(id="boss", name="老板", description="最终决策者", is_boss=True, priority=0)
    ]
    
    # 2. 配置讨论参数
    config = DiscussionConfig(
        max_rounds=10,
        consensus_strategy=ConsensusStrategy.HYBRID,
        turn_order_strategy=TurnOrderStrategy.PRIORITY
    )
    
    # 3. 创建讨论引擎
    engine = DiscussionEngine(
        roles=roles,
        config=config,
        boss_role_id="boss"
    )
    
    # 4. 设置事件回调
    def on_consensus(result):
        print(f"达成共识！置信度: {result.confidence:.2%}")
        print(f"原因: {result.reason}")
    
    def on_boss_intervention(message):
        print(f"老板介入: {message.content}")
    
    engine.on_consensus(on_consensus)
    engine.on_boss_intervention(on_boss_intervention)
    
    # 5. 开始讨论
    await engine.start_discussion("产品功能优先级排序")
    
    # 6. 模拟讨论过程
    while engine.get_current_state() == DiscussionState.ONGOING:
        message = await engine.next_turn()
        if message is None:
            break
        
        # 模拟发言内容（实际应用中由AI生成）
        responses = {
            "pm": "我认为应该优先实现核心功能...",
            "tech": "技术上可行，但需要评估工作量...",
            "design": "从用户体验角度...",
            "boss": "我决定优先做A功能"
        }
        message.content = responses.get(message.sender_id, "继续讨论...")
        
        # 提交消息
        engine.submit_message(message)
        
        print(f"[{message.round_number}] {message.sender_name}: {message.content}")
    
    # 7. 获取讨论结果
    summary = engine.get_summary()
    print(f"\n讨论总结:")
    print(f"主题: {summary.topic}")
    print(f"轮次: {summary.total_rounds}")
    print(f"持续时间: {summary.duration_seconds:.1f}秒")
    print(f"关键观点: {summary.key_points}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 高级用法 - 使用异步运行器

```python
from discussion import AsyncDiscussionRunner

# 创建引擎
engine = DiscussionEngine(roles=roles, config=config)
runner = AsyncDiscussionRunner(engine)

# 设置消息生成器
def generate_message(role, topic):
    # 这里可以调用LLM生成回复
    return f"{role.name}对{topic}的看法是..."

runner.set_message_generator(generate_message)

# 运行讨论
async for message in runner.run(topic="产品规划", max_messages=20):
    print(f"{message.sender_name}: {message.content}")
```

## 共识检测算法详解

### 1. 关键词匹配检测

检测消息中是否包含同意/反对关键词：

```python
detector = KeywordConsensusDetector(
    agreement_keywords=['同意', '赞成', '支持'],
    disagreement_keywords=['反对', '不同意'],
    threshold=0.7  # 70%以上同意即认为达成共识
)
```

### 2. 文本相似度检测

计算所有消息对的平均相似度：

```python
detector = SimilarityConsensusDetector(
    similarity_threshold=0.6,  # 相似度阈值
    min_messages=3             # 最少消息数
)
```

### 3. 投票检测

统计明确的投票结果：

```python
detector = VotingConsensusDetector(
    approval_threshold=0.7,  # 70%同意
    require_all_vote=True    # 要求所有人投票
)

votes = {
    "role1": "agree",
    "role2": "agree",
    "role3": "disagree"
}
result = detector.detect(votes, participants)
```

### 4. 停滞检测

检测讨论是否陷入停滞：

```python
detector = StagnationDetector(
    stagnation_rounds=3,       # 连续3轮
    min_messages_per_round=2   # 每轮至少2条消息
)

# 添加每轮消息
detector.add_round_messages(1, ["观点A", "观点B"])
detector.add_round_messages(2, ["同意A", "支持B"])

# 检测停滞
status = detector.detect_stagnation()
```

### 5. 混合策略（推荐）

综合多种策略，加权计算：

```python
detector = HybridConsensusDetector(
    keyword_threshold=0.7,
    similarity_threshold=0.6,
    voting_threshold=0.7,
    stagnation_rounds=3
)

result = detector.detect(
    messages=["同意", "支持", "赞成"],
    participants=["role1", "role2", "role3"],
    votes={"role1": "agree", "role2": "agree"},
    current_round=5
)
```

## 老板介入检测

老板介入可通过以下方式触发：

1. **角色标识** - 发送者被标记为`is_boss=True`
2. **角色ID匹配** - 发送者ID匹配`boss_role_id`
3. **关键词检测** - 消息包含决策性关键词

配置示例：

```python
config = DiscussionConfig(
    boss_intervention_keywords=[
        '我决定', '听我的', '就这样', '执行', '定下来',
        'i decide', 'final decision', 'execute'
    ]
)
```

## 状态流转图

```
                    +-----------+
                    |  PENDING  |
                    +-----+-----+
                          |
                          v
                    +-----------+
         +--------->|  ONGOING  |<---------+
         |          +-----+-----+          |
         |                |                |
         |    +-----------+-----------+    |
         |    |           |           |    |
         v    v           v           v    v
   +-----------+  +-----------+  +-----------+
   | CONSENSUS |  |   BOSS    |  |  ROUNDS   |
   |  REACHED  |  |  NEEDED   |  | EXHAUSTED |
   +-----------+  +-----------+  +-----------+
```

## 性能考虑

- **消息存储** - 使用索引结构，支持O(1)按轮次/发送者/类型查询
- **共识检测** - 相似度计算为O(n²)，建议限制消息数量
- **轮次限制** - 默认20轮，可根据场景调整

## 扩展建议

1. **LLM集成** - 将`LLM_JUDGE`策略接入实际LLM进行判断
2. **持久化** - 添加数据库存储讨论历史
3. **可视化** - 添加讨论流程可视化组件
4. **多语言** - 扩展关键词检测支持更多语言
