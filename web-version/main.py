"""
AI虚拟软件公司 - 主入口

启动后端API服务和WebSocket服务器
"""
import argparse
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import run_server, app
from backend.storage import storage, PhaseType
from backend.websocket import manager
from backend.reminder import reminder_service
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI虚拟软件公司后端服务')
    parser.add_argument(
        '--host', 
        type=str, 
        default='0.0.0.0',
        help='服务器主机地址 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8000,
        help='服务器端口 (默认: 8000)'
    )
    parser.add_argument(
        '--reload', 
        action='store_true',
        help='启用热重载（开发模式）'
    )
    parser.add_argument(
        '--init-phase',
        type=str,
        default='requirement',
        choices=['requirement', 'design', 'coding', 'testing', 'deployment', 'completed'],
        help='初始化阶段 (默认: requirement)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 AI虚拟软件公司后端服务")
    print("=" * 60)
    print(f"📡 服务器地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔌 WebSocket: ws://{args.host}:{args.port}/ws")
    print(f"👔 老板WebSocket: ws://{args.host}:{args.port}/ws/boss")
    print("=" * 60)
    
    # 启动服务器
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
