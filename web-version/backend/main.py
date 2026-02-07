"""
FastAPI主应用 - 后端API服务入口
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .storage import storage, PhaseType
from .websocket import manager, websocket_endpoint
from .api import router as api_router
from .reminder import reminder_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 启动时间
START_TIME = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动和关闭时执行的操作
    """
    # 启动时
    logger.info("=" * 50)
    logger.info("AI虚拟软件公司后端服务启动中...")
    logger.info("=" * 50)
    
    # 初始化阶段
    storage.set_current_phase(PhaseType.REQUIREMENT)
    logger.info(f"当前阶段: {storage.get_current_phase().name}")
    
    # 启动提醒服务
    reminder_service.start()
    
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


# ============ 根端点 ============

@app.get("/")
async def root():
    """根端点 - 返回API信息"""
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
