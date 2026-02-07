#!/usr/bin/env python3
"""
MetaGPT Agent Company - 主程序入口
===================================

AI驱动的虚拟软件公司，实现9阶段软件开发流程：
1. 需求分析 -> 2. 技术方案设计 -> 3. UI/UX设计 -> 4. 任务拆解
5. 编码实现 -> 6. UI验收 -> 7. 功能测试 -> 8. 部署上线 -> 9. 运维监控

使用方法:
    python main.py                          # 启动Web服务器
    python main.py --demo                   # 运行演示项目
    python main.py --phase P1 --idea "..."  # 运行单个阶段
    python main.py --config config.yaml     # 指定配置文件
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Optional

# 添加项目路径
sys.path.insert(0, '/mnt/okcomputer/output')

# 导入公司模块
from company import AgentCompany, CompanyConfig, WorkflowManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='MetaGPT Agent Company - AI驱动的虚拟软件公司',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py                          # 启动Web服务器
  python main.py --demo                   # 运行演示项目
  python main.py --idea "开发一个待办事项应用"  # 启动指定项目
  python main.py --phase P1 --idea "..."  # 只运行需求分析阶段
  python main.py --config custom.yaml     # 使用自定义配置
        '''
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='/mnt/okcomputer/output/config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示项目'
    )
    
    parser.add_argument(
        '--idea', '-i',
        type=str,
        help='项目需求/想法'
    )
    
    parser.add_argument(
        '--phase', '-p',
        type=str,
        choices=['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'],
        help='只运行指定阶段 (P1-P9)'
    )
    
    parser.add_argument(
        '--name', '-n',
        type=str,
        help='项目名称'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='启动Web服务器'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web服务器主机 (默认: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Web服务器端口 (默认: 8000)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./outputs',
        help='输出目录 (默认: ./outputs)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """设置日志级别"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)
    
    # 设置第三方库日志级别
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def load_config(config_path: str) -> CompanyConfig:
    """加载配置文件"""
    if not os.path.exists(config_path):
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return CompanyConfig()
    
    return CompanyConfig.from_yaml(config_path)


async def run_demo_project(company: AgentCompany):
    """运行演示项目"""
    idea = """
开发一个简单的待办事项管理应用，功能需求如下：
1. 用户可以添加新的待办任务
2. 用户可以标记任务为已完成
3. 用户可以删除任务
4. 支持任务优先级设置（高/中/低）
5. 支持按状态筛选任务（全部/进行中/已完成）
6. 数据需要持久化存储
7. 界面简洁美观，易于使用

技术约束：
- 使用Python开发
- Web界面使用现代前端框架
- 数据库使用SQLite
"""
    
    logger.info("=" * 60)
    logger.info("启动演示项目: 待办事项管理应用")
    logger.info("=" * 60)
    
    result = await company.start_project(idea, "TodoApp Demo")
    
    logger.info("=" * 60)
    logger.info("项目执行结果:")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    logger.info("=" * 60)
    
    return result


async def run_single_phase(company: AgentCompany, phase_id: str, idea: str):
    """运行单个阶段"""
    logger.info(f"运行阶段: {phase_id}")
    
    result = await company.run_single_phase(phase_id, idea)
    
    logger.info("=" * 60)
    logger.info(f"阶段 {result.phase_name} 执行结果:")
    logger.info(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    logger.info("=" * 60)
    
    return result


async def run_full_project(company: AgentCompany, idea: str, project_name: Optional[str] = None):
    """运行完整项目"""
    logger.info("=" * 60)
    logger.info(f"启动项目: {project_name or 'Unnamed Project'}")
    logger.info("=" * 60)
    
    result = await company.start_project(idea, project_name)
    
    logger.info("=" * 60)
    logger.info("项目执行结果:")
    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    logger.info("=" * 60)
    
    return result


def start_web_server(company: AgentCompany, host: str, port: int):
    """启动Web服务器"""
    try:
        import uvicorn
        from fastapi import FastAPI
        
        app = company.create_web_app()
        
        if app is None:
            logger.error("无法创建Web应用，请确保已安装FastAPI")
            return
        
        logger.info(f"启动Web服务器: http://{host}:{port}")
        logger.info(f"飞书Webhook: http://{host}:{port}/webhook/feishu")
        logger.info(f"健康检查: http://{host}:{port}/health")
        
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        logger.error("未安装uvicorn，无法启动Web服务器")
        logger.error("请运行: pip install uvicorn[standard]")


async def interactive_mode(company: AgentCompany):
    """交互模式"""
    print("\n" + "=" * 60)
    print("MetaGPT Agent Company - 交互模式")
    print("=" * 60)
    print("命令:")
    print("  start <idea>  - 启动新项目")
    print("  status        - 查看当前状态")
    print("  phases        - 查看阶段列表")
    print("  roles         - 查看角色列表")
    print("  stop          - 停止当前项目")
    print("  quit          - 退出")
    print("=" * 60 + "\n")
    
    while True:
        try:
            command = input("AgentCompany> ").strip()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd == "quit" or cmd == "exit":
                print("再见!")
                break
            
            elif cmd == "status":
                status = company.get_status()
                print(json.dumps(status, ensure_ascii=False, indent=2))
            
            elif cmd == "phases":
                phases = company.get_phases()
                print(json.dumps(phases, ensure_ascii=False, indent=2))
            
            elif cmd == "roles":
                roles = company.get_roles()
                print(json.dumps(roles, ensure_ascii=False, indent=2))
            
            elif cmd == "start":
                if not arg:
                    print("请提供项目需求，例如: start 开发一个待办事项应用")
                    continue
                result = await run_full_project(company, arg)
                print(f"\n项目结果: {result}")
            
            elif cmd == "stop":
                company.stop_project()
                print("项目已停止")
            
            else:
                print(f"未知命令: {cmd}")
        
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")


async def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 加载配置
    config = load_config(args.config)
    
    # 覆盖输出目录
    if args.output:
        config.output_dir = args.output
        os.makedirs(config.output_dir, exist_ok=True)
    
    # 创建公司实例
    logger.info("初始化 Agent Company...")
    company = AgentCompany(config)
    
    # 根据参数执行相应操作
    if args.web:
        # 启动Web服务器（阻塞）
        start_web_server(company, args.host, args.port)
    
    elif args.demo:
        # 运行演示项目
        await run_demo_project(company)
    
    elif args.phase:
        # 运行单个阶段
        idea = args.idea or input("请输入项目需求: ")
        await run_single_phase(company, args.phase, idea)
    
    elif args.idea:
        # 运行完整项目
        await run_full_project(company, args.idea, args.name)
    
    else:
        # 交互模式
        await interactive_mode(company)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已终止")
    except Exception as e:
        logger.exception("程序执行失败")
        sys.exit(1)
