"""
API路由模块 - 定义RESTful API端点
"""
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
import logging

from .storage import storage, Message, PhaseType, Phase
from .websocket import manager, WebSocketMessage
from .reminder import reminder_service

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api")


# ============ Pydantic模型 ============

class IdeaRequest(BaseModel):
    """需求提交请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="需求描述")
    title: Optional[str] = Field(None, max_length=200, description="需求标题")
    priority: str = Field("normal", description="优先级: low, normal, high")


class IdeaResponse(BaseModel):
    """需求提交响应"""
    success: bool
    message: str
    idea_id: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    role: str
    content: str
    phase: str
    timestamp: str
    message_type: str
    metadata: dict
    is_mention_boss: bool


class PhaseResponse(BaseModel):
    """阶段响应"""
    id: str
    name: str
    description: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]


class RoleInfo(BaseModel):
    """角色信息"""
    id: str
    name: str
    description: str
    responsibilities: List[str]
    avatar: Optional[str] = None


class StatusResponse(BaseModel):
    """系统状态响应"""
    status: str
    current_phase: str
    message_count: int
    connection_count: int
    boss_connected: bool
    reminder_status: dict
    uptime: str


class MessagesListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]
    total: int
    offset: int
    limit: int
    has_more: bool


# ============ 角色定义 ============

ROLES = [
    RoleInfo(
        id="pm",
        name="产品经理 (PM)",
        description="负责需求分析和产品规划",
        responsibilities=[
            "分析用户需求",
            "编写需求文档",
            "制定产品规划",
            "协调团队沟通"
        ],
        avatar="👨‍💼"
    ),
    RoleInfo(
        id="architect",
        name="架构师 (Architect)",
        description="负责系统架构设计",
        responsibilities=[
            "设计系统架构",
            "制定技术方案",
            "设计数据库结构",
            "规划API接口"
        ],
        avatar="👨‍🔧"
    ),
    RoleInfo(
        id="developer",
        name="开发工程师 (Developer)",
        description="负责代码实现",
        responsibilities=[
            "编写业务代码",
            "实现功能模块",
            "修复代码缺陷",
            "代码重构优化"
        ],
        avatar="👨‍💻"
    ),
    RoleInfo(
        id="tester",
        name="测试工程师 (Tester)",
        description="负责测试验证",
        responsibilities=[
            "编写测试用例",
            "执行功能测试",
            "进行性能测试",
            "提交缺陷报告"
        ],
        avatar="👩‍🔬"
    ),
    RoleInfo(
        id="boss",
        name="老板 (Boss)",
        description="项目负责人，拥有最终决策权",
        responsibilities=[
            "审批重要决策",
            "解答团队疑问",
            "确认需求变更",
            "验收项目成果"
        ],
        avatar="👔"
    )
]


# ============ API端点 ============

@router.get("/phases", response_model=List[PhaseResponse])
async def get_all_phases():
    """
    获取所有阶段信息
    
    Returns:
        阶段列表
    """
    phases = storage.get_all_phases()
    return [phase.to_dict() for phase in phases]


@router.get("/phase/current", response_model=PhaseResponse)
async def get_current_phase():
    """
    获取当前阶段
    
    Returns:
        当前阶段信息
    """
    phase = storage.get_current_phase()
    return phase.to_dict()


@router.post("/phase/{phase_id}")
async def set_phase(phase_id: str):
    """
    设置当前阶段（用于阶段切换）
    
    Args:
        phase_id: 阶段ID
        
    Returns:
        新阶段信息
    """
    try:
        phase = PhaseType(phase_id)
        new_phase = storage.set_current_phase(phase)
        
        # 广播阶段变更
        await manager.broadcast_phase_change(phase, new_phase.to_dict())
        
        logger.info(f"阶段切换至: {phase_id}")
        return {
            "success": True,
            "message": f"阶段已切换至: {new_phase.name}",
            "phase": new_phase.to_dict()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的阶段ID: {phase_id}")


@router.get("/messages", response_model=MessagesListResponse)
async def get_messages(
    phase: Optional[str] = Query(None, description="按阶段筛选"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取历史消息
    
    Args:
        phase: 阶段筛选（可选）
        role: 角色筛选（可选）
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        消息列表
    """
    phase_type = None
    if phase:
        try:
            phase_type = PhaseType(phase)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的阶段: {phase}")
    
    messages = storage.get_messages(
        phase=phase_type,
        role=role,
        limit=limit,
        offset=offset
    )
    
    total = storage.get_message_count(phase=phase_type, role=role)
    
    return {
        "messages": [msg.to_dict() for msg in messages],
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total
    }


@router.post("/idea", response_model=IdeaResponse)
async def submit_idea(request: IdeaRequest):
    """
    提交新需求
    
    Args:
        request: 需求请求
        
    Returns:
        提交结果
    """
    try:
        # 创建需求消息
        idea_id = f"idea_{datetime.now().timestamp()}"
        
        # 重置到需求分析阶段
        storage.set_current_phase(PhaseType.REQUIREMENT)
        
        # 创建用户消息
        message = Message(
            id=idea_id,
            role="User",
            content=f"【{request.title or '新需求'}】\n{request.content}",
            phase=PhaseType.REQUIREMENT,
            timestamp=datetime.now(),
            message_type="idea",
            metadata={
                "title": request.title,
                "priority": request.priority
            }
        )
        
        storage.add_message(message)
        
        # 广播新需求
        await manager.broadcast(WebSocketMessage(
            type="new_idea",
            data={
                "idea_id": idea_id,
                "title": request.title,
                "content": request.content,
                "priority": request.priority
            }
        ))
        
        logger.info(f"新需求提交: {idea_id}")
        
        return IdeaResponse(
            success=True,
            message="需求已提交，正在开始分析...",
            idea_id=idea_id
        )
        
    except Exception as e:
        logger.error(f"提交需求失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


@router.get("/roles", response_model=List[RoleInfo])
async def get_all_roles():
    """
    获取所有角色信息
    
    Returns:
        角色列表
    """
    return ROLES


@router.get("/roles/{role_id}", response_model=RoleInfo)
async def get_role(role_id: str):
    """
    获取指定角色信息
    
    Args:
        role_id: 角色ID
        
    Returns:
        角色信息
    """
    for role in ROLES:
        if role.id == role_id:
            return role
    
    raise HTTPException(status_code=404, detail=f"角色不存在: {role_id}")


@router.get("/status", response_model=StatusResponse)
async def get_system_status():
    """
    获取系统状态
    
    Returns:
        系统状态信息
    """
    current_phase = storage.get_current_phase()
    
    return StatusResponse(
        status="running",
        current_phase=current_phase.id.value,
        message_count=len(storage._messages),
        connection_count=manager.connection_count,
        boss_connected=manager.has_boss_connection,
        reminder_status=reminder_service.get_reminder_status(),
        uptime=datetime.now().isoformat()
    )


@router.post("/messages/send")
async def send_message(
    role: str,
    content: str,
    message_type: str = "text",
    metadata: dict = None
):
    """
    发送消息（用于AI角色发送消息）
    
    Args:
        role: 发送者角色
        content: 消息内容
        message_type: 消息类型
        metadata: 额外元数据
        
    Returns:
        发送结果
    """
    try:
        current_phase = storage.get_current_phase()
        
        # 检查是否@老板
        is_mention = reminder_service.is_mention_boss(content)
        
        # 广播消息
        message = await manager.broadcast_message(
            role=role,
            content=content,
            phase=current_phase.id,
            message_type=message_type,
            metadata=metadata or {},
            is_mention_boss=is_mention
        )
        
        # 如果需要提醒
        if is_mention:
            await reminder_service.handle_new_message(message)
        
        return {
            "success": True,
            "message_id": message.id,
            "is_mention_boss": is_mention
        }
        
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


@router.post("/boss/reply")
async def boss_reply(content: str):
    """
    老板回复（用于API方式发送老板消息）
    
    Args:
        content: 回复内容
        
    Returns:
        发送结果
    """
    try:
        current_phase = storage.get_current_phase()
        
        # 创建老板消息
        message = Message(
            id=f"boss_{datetime.now().timestamp()}",
            role="Boss",
            content=content,
            phase=current_phase.id,
            timestamp=datetime.now(),
            message_type="text",
            metadata={"source": "api"}
        )
        
        storage.add_message(message)
        
        # 广播消息
        await manager.broadcast(WebSocketMessage(
            type="boss_message",
            data=message.to_dict()
        ))
        
        # 处理老板回复（取消提醒）
        await reminder_service.handle_new_message(message)
        
        return {
            "success": True,
            "message_id": message.id
        }
        
    except Exception as e:
        logger.error(f"老板回复失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送失败: {str(e)}")


@router.get("/mentions/unanswered")
async def get_unanswered_mentions():
    """
    获取未回复的@老板消息
    
    Returns:
        未回复消息列表
    """
    since = datetime.now() - timedelta(minutes=30)
    mentions = storage.get_unanswered_mentions(since)
    
    return {
        "mentions": [msg.to_dict() for msg in mentions],
        "count": len(mentions)
    }


@router.post("/system/clear")
async def clear_system():
    """
    清空系统数据（重置）
    
    Returns:
        操作结果
    """
    try:
        storage.clear_messages()
        
        # 广播重置消息
        await manager.send_system_message("系统已重置", {"action": "clear"})
        
        return {
            "success": True,
            "message": "系统数据已清空"
        }
        
    except Exception as e:
        logger.error(f"清空系统失败: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }