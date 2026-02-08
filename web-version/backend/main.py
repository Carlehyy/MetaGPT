"""
FastAPI主应用 - 后端API服务入口
"""
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .storage import storage, PhaseType
from .websocket import manager, websocket_endpoint
from .api import router as api_router
from .reminder import reminder_service

# 导入讨论引擎和角色
from discussion.engine import DiscussionEngine
from roles import (
    Boss, ProductManager, Architect, ProductDesigner,
    ProjectManager, Engineer, QAEngineer, DevOps,
    Phase, Role
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 启动时间
START_TIME = datetime.now()

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 全局讨论引擎实例
discussion_engine: DiscussionEngine = None


async def handle_boss_message(message):
    """
    处理老板发送的消息

    当老板发送消息后，触发AI角色讨论
    """
    global discussion_engine

    logger.info(f"收到老板消息: {message.content[:50]}...")

    # 检查是否是需求消息（包含关键词）
    content = message.content.lower()
    is_requirement = any(keyword in content for keyword in [
        "需求", "开发", "产品", "功能", "系统", "app", "网站", "平台",
        "需要", "想要", "做一个", "设计一个", "实现"
    ])

    if is_requirement and discussion_engine:
        logger.info("检测到需求消息，启动AI角色讨论...")

        # 获取当前阶段
        current_phase = storage.get_current_phase()
        phase_enum = Phase(current_phase.id.value)

        # 启动讨论
        asyncio.create_task(
            discussion_engine.start_discussion(
                phase=phase_enum,
                topic=f"讨论需求: {message.content[:30]}...",
                initial_message=message.content
            )
        )
    else:
        logger.info("非需求消息，仅广播给所有客户端")


def init_discussion_engine():
    """
    初始化讨论引擎

    注册所有AI角色和消息回调
    """
    global discussion_engine

    logger.info("初始化讨论引擎...")

    # 创建讨论引擎
    discussion_engine = DiscussionEngine(
        max_rounds=5,
        consensus_threshold=2,
        auto_invite_boss=True
    )

    # 注册所有AI角色
    roles = [
        ProductManager(),
        Architect(),
        ProductDesigner(),
        ProjectManager(),
        Engineer(),
        QAEngineer(),
        DevOps(),
    ]

    for role in roles:
        discussion_engine.register_role(role)
        logger.info(f"注册角色: {role.name}")

# 注册消息回调 - 将AI消息广播到WebSocket
    def broadcast_ai_message(message):
        """广播AI消息到所有客户端"""
        from backend.websocket import WebSocketMessage
        import asyncio

        # 获取发送者角色
        sender_role = message.sender if hasattr(message, "sender") and message.sender else message.role

        # 创建WebSocket消息
        ws_message = WebSocketMessage(
            type="ai_message",
            data={
                "id": message.id if hasattr(message, "id") else str(datetime.now().timestamp()),
                "role": sender_role,
                "content": message.content,
                "timestamp": datetime.now().isoformat(),
                "phase": storage.get_current_phase().id.value
            }
        )

        # 使用asyncio.create_task执行异步广播
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast(ws_message))
            else:
                loop.run_until_complete(manager.broadcast(ws_message))
        except Exception as e:
            logger.error(f"广播消息失败: {e}")

        # 同时存储到storage
        from backend.storage import Message as StorageMessage
        storage_msg = StorageMessage(
            id=message.id if hasattr(message, "id") else str(datetime.now().timestamp()),
            role=sender_role,
            content=message.content,
            phase=storage.get_current_phase().id,
            timestamp=datetime.now(),
            message_type="text",
            metadata={"source": "ai"}
        )
        storage.add_message(storage_msg)

        logger.info(f"AI角色 [{sender_role}] 发言: {message.content[:50]}...")

    discussion_engine.add_message_callback(broadcast_ai_message)

    logger.info(f"讨论引擎初始化完成，已注册 {len(roles)} 个AI角色")

    return discussion_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动和关闭时执行的操作
    """
    global discussion_engine

    # 启动时
    logger.info("=" * 50)
    logger.info("AI虚拟软件公司后端服务启动中...")
    logger.info("=" * 50)

    # 初始化阶段
    storage.set_current_phase(PhaseType.REQUIREMENT)
    logger.info(f"当前阶段: {storage.get_current_phase().name}")

    # 启动提醒服务
    reminder_service.start()

    # 初始化讨论引擎
    init_discussion_engine()

    # 注册老板消息处理器
    manager.register_boss_message_handler(handle_boss_message)
    logger.info("老板消息处理器已注册")

    logger.info("服务启动完成，等待连接...")

    yield

    # 关闭时
    logger.info("服务正在关闭...")

    # 停止提醒服务
    reminder_service.stop()

    logger.info("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI虚拟软件公司 API",
    description="AI虚拟软件公司后端API服务 - 支持WebSocket实时通信",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境应该限制）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 配置模板
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 注册API路由
app.include_router(api_router)


# ============ WebSocket端点 ============

@app.websocket("/ws")
async def websocket_general(websocket: WebSocket):
    """
    普通客户端WebSocket连接

    用于AI角色和观察者连接
    """
    await websocket_endpoint(websocket, is_boss=False)


@app.websocket("/ws/boss")
async def websocket_boss(websocket: WebSocket):
    """
    老板专用WebSocket连接

    用于老板发送消息和接收提醒
    """
    await websocket_endpoint(websocket, is_boss=True)


# ============ 根端点 - 返回前端页面 ============

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根端点 - 返回前端页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "name": "AI虚拟软件公司 API",
        "version": "1.0.0",
        "description": "AI虚拟软件公司后端API服务",
        "docs": "/docs",
        "redoc": "/redoc",
        "websocket": {
            "general": "/ws",
            "boss": "/ws/boss"
        }
    }


@app.get("/info")
async def info():
    """获取系统详细信息"""
    uptime = datetime.now() - START_TIME
    current_phase = storage.get_current_phase()

    return {
        "name": "AI虚拟软件公司 API",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": uptime.total_seconds(),
        "uptime_formatted": str(uptime).split('.')[0],
        "current_phase": {
            "id": current_phase.id.value,
            "name": current_phase.name,
            "status": current_phase.status
        },
        "connections": {
            "total": manager.connection_count,
            "boss_connected": manager.has_boss_connection
        },
        "messages": {
            "total": len(storage._messages),
            "current_phase": len(storage.get_messages_by_phase(current_phase.id))
        },
        "reminder_service": reminder_service.get_reminder_status()
    }


# ============ 错误处理 ============

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============ 启动函数 ============

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    启动服务器

    Args:
        host: 主机地址
        port: 端口号
        reload: 是否启用热重载
    """
    import uvicorn

    logger.info(f"启动服务器: {host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
