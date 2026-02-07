# AI Team API 文档

本文档介绍 AI Team 的核心 API 接口。

---

## AgentCompany API

### 类定义

```python
class AgentCompany:
    def __init__(self, config: CompanyConfig)
    async def start_project(self, idea: str, chat_id: str) -> None
    async def start_phase(self, phase_idx: int, chat_id: str) -> None
    async def handle_message(self, sender: str, content: str, chat_id: str) -> None
    async def close(self) -> None
```

### 方法说明

#### `__init__(config)`

初始化公司实例。

**参数**：
- `config` (CompanyConfig): 公司配置

**示例**：
```python
config = CompanyConfig(
    llm_api_key="your_key",
    feishu_app_id="your_app_id",
    feishu_app_secret="your_secret"
)
company = AgentCompany(config)
```

---

#### `start_project(idea, chat_id)`

启动新项目。

**参数**：
- `idea` (str): 项目需求描述
- `chat_id` (str): 飞书群聊ID

**示例**：
```python
await company.start_project(
    idea="开发一个智能客服系统",
    chat_id="oc_xxx"
)
```

---

#### `start_phase(phase_idx, chat_id)`

开始指定阶段。

**参数**：
- `phase_idx` (int): 阶段索引（0-8）
- `chat_id` (str): 飞书群聊ID

**示例**：
```python
await company.start_phase(0, "oc_xxx")  # 开始需求分析阶段
```

---

#### `handle_message(sender, content, chat_id)`

处理用户消息。

**参数**：
- `sender` (str): 发送者名称
- `content` (str): 消息内容
- `chat_id` (str): 群聊ID

**示例**：
```python
await company.handle_message(
    sender="产品经理",
    content="我分析了这个需求...",
    chat_id="oc_xxx"
)
```

---

## DiscussionEngine API

### 类定义

```python
class DiscussionEngine:
    def __init__(
        self,
        participants: List[Dict],
        phase: str,
        config: Optional[DiscussionConfig] = None
    )
    async def start_discussion(self, topic: str) -> bool
    async def next_turn(self, speaker_override: Optional[str] = None) -> Optional[Dict]
    async def add_message(self, sender: str, content: str, msg_type: str = "text") -> DiscussionMessage
    async def boss_intervene(self, decision: str)
    async def terminate(self)
    def register_message_callback(self, callback: Callable)
    def register_state_callback(self, callback: Callable)
    def get_discussion_summary(self) -> Dict
```

### 方法说明

#### `start_discussion(topic)`

开始讨论。

**参数**：
- `topic` (str): 讨论主题

**返回**：
- `bool`: 是否成功开始

---

#### `next_turn(speaker_override)`

获取下一个发言者。

**参数**：
- `speaker_override` (str, optional): 指定发言者名称

**返回**：
- `Dict`: 发言者信息 `{"name": "", "role": "", "round": 1}`

---

#### `add_message(sender, content, msg_type)`

添加消息。

**参数**：
- `sender` (str): 发送者名称
- `content` (str): 消息内容
- `msg_type` (str): 消息类型 (`text`, `agree`, `disagree`, `pass`)

**返回**：
- `DiscussionMessage`: 消息对象

---

#### `register_message_callback(callback)`

注册消息回调函数。

**参数**：
- `callback` (Callable): 回调函数，接收 `DiscussionMessage` 参数

**示例**：
```python
def on_message(message):
    print(f"{message.sender}: {message.content}")

engine.register_message_callback(on_message)
```

---

#### `register_state_callback(callback)`

注册状态回调函数。

**参数**：
- `callback` (Callable): 回调函数，接收 `DiscussionStatus` 参数

**示例**：
```python
def on_state_change(status):
    print(f"状态变更: {status.state.value}")

engine.register_state_callback(on_state_change)
```

---

#### `get_discussion_summary()`

获取讨论摘要。

**返回**：
- `Dict`: 摘要信息

```python
{
    "phase": "需求分析",
    "state": "consensus_reached",
    "rounds": 3,
    "participants": ["产品经理", "架构师"],
    "message_count": 10,
    "consensus_reason": "达到显式同意阈值"
}
```

---

## FeishuBot API

### 类定义

```python
class FeishuBot:
    def __init__(self, config: FeishuConfig)
    async def get_access_token(self) -> str
    async def send_text_message(self, receive_id: str, content: str) -> Dict
    async def send_card_message(self, receive_id: str, card_content: Dict) -> Dict
    async def create_chat(self, name: str, description: str = "") -> Dict
    async def add_chat_members(self, chat_id: str, user_ids: List[str]) -> Dict
    async def get_chat_info(self, chat_id: str) -> Dict
    def register_message_handler(self, handler: Callable)
    async def close(self)
```

### 方法说明

#### `send_text_message(receive_id, content)`

发送文本消息。

**参数**：
- `receive_id` (str): 接收者ID（群聊ID或用户ID）
- `content` (str): 消息内容

**返回**：
- `Dict`: 发送结果

---

#### `send_card_message(receive_id, card_content)`

发送卡片消息。

**参数**：
- `receive_id` (str): 接收者ID
- `card_content` (Dict): 卡片内容

**返回**：
- `Dict`: 发送结果

**示例**：
```python
card = CardBuilder.build_discussion_card(
    phase="需求分析",
    round_num=1,
    speaker="产品经理",
    content="我分析了这个需求...",
    participants=[...]
)
await bot.send_card_message("oc_xxx", card)
```

---

#### `create_chat(name, description)`

创建群聊。

**参数**：
- `name` (str): 群聊名称
- `description` (str): 群聊描述

**返回**：
- `Dict`: 创建结果，包含 `chat_id`

---

## CardBuilder API

### 类定义

```python
class CardBuilder:
    @staticmethod
    def build_discussion_card(
        phase: str,
        round_num: int,
        speaker: str,
        speaker_avatar: str,
        content: str,
        participants: List[Dict],
        consensus_status: str = "讨论中"
    ) -> Dict
    
    @staticmethod
    def build_welcome_card() -> Dict
    
    @staticmethod
    def build_phase_summary_card(
        phase: str,
        summary: str,
        next_phase: str
    ) -> Dict
```

---

## WorkflowManager API

### 类定义

```python
class WorkflowManager:
    def __init__(self)
    async def start_workflow(self, project_context: Dict)
    def get_current_phase(self) -> Optional[Dict]
    def get_phase_progress(self) -> Dict
    def register_phase_callback(self, callback: Callable)
```

### 方法说明

#### `get_current_phase()`

获取当前阶段。

**返回**：
- `Dict`: 阶段信息 `{"id": "P1", "name": "需求分析", "leader": "产品经理"}`

---

#### `get_phase_progress()`

获取阶段进度。

**返回**：
- `Dict`: 进度信息

```python
{
    "total": 9,
    "completed": 3,
    "current": 4,
    "percentage": 33.3
}
```

---

## 配置类

### CompanyConfig

```python
@dataclass
class CompanyConfig:
    llm_api_key: str = ""
    llm_model: str = "glm-4"
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    max_rounds_per_phase: int = 20
    consensus_threshold: float = 0.8
```

### DiscussionConfig

```python
@dataclass
class DiscussionConfig:
    max_rounds: int = 20
    consensus_threshold: float = 0.8
    enable_llm_judgment: bool = True
    pass_threshold: int = 3
    content_similarity_threshold: float = 0.9
    stagnation_rounds: int = 3
    boss_intervention_timeout: int = 300
    consensus_strategy: str = "HYBRID"
```

### FeishuConfig

```python
@dataclass
class FeishuConfig:
    app_id: str
    app_secret: str
    verification_token: Optional[str] = None
```

---

## 枚举类型

### DiscussionState

```python
class DiscussionState(Enum):
    PENDING = "pending"
    ONGOING = "ongoing"
    CONSENSUS_REACHED = "consensus_reached"
    BOSS_NEEDED = "boss_needed"
    ROUNDS_EXHAUSTED = "rounds_exhausted"
    PAUSED = "paused"
    TERMINATED = "terminated"
```

### ParticipationType

```python
class ParticipationType(Enum):
    LEAD = "负责/执行"
    CONSULT = "咨询"
    INFORM = "知会"
    NONE = "-"
```

---

## 完整示例

```python
import asyncio
from company import AgentCompany, CompanyConfig

async def main():
    # 创建配置
    config = CompanyConfig(
        llm_api_key="your_key",
        feishu_app_id="your_app_id",
        feishu_app_secret="your_secret"
    )
    
    # 创建公司实例
    company = AgentCompany(config)
    
    # 启动项目
    await company.start_project(
        idea="开发一个智能客服系统",
        chat_id="oc_xxx"
    )
    
    # 模拟讨论
    await company.handle_message(
        sender="产品经理",
        content="我分析了这个需求...",
        chat_id="oc_xxx"
    )
    
    # 关闭
    await company.close()

if __name__ == "__main__":
    asyncio.run(main())
```
