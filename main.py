#!/usr/bin/env python3
"""
AI Team - 智能软件开发团队
主程序入口

AI Team 是一个由8个AI角色组成的虚拟软件公司，
通过群聊讨论协作完成从需求分析到运维监控的完整软件开发生命周期。
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
import yaml

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from company.agent_company import AgentCompany, CompanyConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path='config.yaml'):
    """加载配置文件"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"无法加载配置文件 {config_path}: {e}")
        return None


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='AI Team - 智能软件开发团队',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --demo                    # 运行演示模式
  python main.py --idea "开发一个待办应用"  # 启动新项目
  python main.py --config custom.yaml      # 使用自定义配置
        """
    )
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--idea', type=str, help='项目需求描述')
    parser.add_argument('--config', type=str, default='config.yaml', help='配置文件路径')
    parser.add_argument('--feishu-app-id', type=str, default='', help='飞书App ID')
    parser.add_argument('--feishu-app-secret', type=str, default='', help='飞书App Secret')
    parser.add_argument('--llm-api-key', type=str, default='', help='LLM API Key')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')

    return parser.parse_args()


async def run_demo():
    """运行演示"""
    logger.info("=" * 60)
    logger.info("🎉 AI Team - 演示模式")
    logger.info("=" * 60)

    # 加载配置
    config_data = load_config('config.yaml')

    if config_data:
        feishu_config = config_data.get('feishu', {})
        llm_config = config_data.get('llm', {})

        # 创建公司配置（使用真实配置，演示模式）
        config = CompanyConfig(
            llm_api_key=llm_config.get('api_key', 'demo_key'),
            feishu_app_id=feishu_config.get('app_id', 'demo_app_id'),
            feishu_app_secret=feishu_config.get('app_secret', 'demo_app_secret'),
            demo_mode=True
        )
        logger.info("✅ 已加载配置文件")
    else:
        logger.warning("⚠️ 未找到配置文件，使用演示配置")
        config = CompanyConfig(
            llm_api_key="demo_key",
            feishu_app_id="demo_app_id",
            feishu_app_secret="demo_app_secret"
        )

    # 创建公司实例
    company = AgentCompany(config)

    # 模拟项目需求
    idea = "开发一个智能待办事项管理应用，支持语音输入、智能分类和提醒功能"

    logger.info(f"\n📋 项目需求: {idea}\n")

    # 模拟群聊ID
    chat_id = "demo_chat_001"

    try:
        # 启动项目
        await company.start_project(idea, chat_id)

        # 模拟讨论过程
        logger.info("🗣️ 模拟讨论过程...\n")

        # 模拟几个角色的发言
        messages = [
            ("产品经理", "我分析了这个需求，核心功能包括：1.语音输入 2.智能分类 3.提醒功能。建议先完成MVP版本。"),
            ("架构师", "技术方案上，我建议使用React Native开发跨平台应用，后端使用Python FastAPI，数据库用PostgreSQL。"),
            ("产品设计师", "UI设计方面，我建议采用简洁的卡片式布局，支持深色模式，主色调使用蓝色系。"),
            ("项目经理", "项目计划：第一周完成需求确认，第二周完成设计，第三四周开发，第五周测试上线。"),
            ("开发工程师", "技术实现没问题，我可以负责前端开发，需要后端同学配合API接口。"),
            ("测试工程师", "测试策略：单元测试覆盖率80%以上，集成测试覆盖核心流程，还需要进行性能测试。"),
            ("运维工程师", "部署方案：使用Docker容器化部署，Kubernetes管理，监控用Prometheus+Grafana。"),
            ("老板", "方案不错，按计划执行，注意控制成本和质量。")
        ]

        for sender, content in messages:
            logger.info(f"[{sender}] {content[:50]}...")
            await company.handle_message(sender, content, chat_id)
            await asyncio.sleep(0.5)

        logger.info("\n" + "=" * 60)
        logger.info("✅ 演示完成！")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"演示异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await company.close()


async def run_with_idea(idea: str, app_id: str, app_secret: str, api_key: str):
    """使用指定需求运行"""
    logger.info(f"🚀 启动项目: {idea}")

    # 加载配置
    config_data = load_config('config.yaml')

    # 使用命令行参数或配置文件
    if not app_id and config_data:
        app_id = config_data.get('feishu', {}).get('app_id', '')
    if not app_secret and config_data:
        app_secret = config_data.get('feishu', {}).get('app_secret', '')
    if not api_key and config_data:
        api_key = config_data.get('llm', {}).get('api_key', '')

    config = CompanyConfig(
        llm_api_key=api_key or "demo_key",
        feishu_app_id=app_id or "demo_app_id",
        feishu_app_secret=app_secret or "demo_app_secret"
    )

    company = AgentCompany(config)

    try:
        chat_id = "demo_chat_001"
        await company.start_project(idea, chat_id)

        # 保持运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        await company.close()


async def main():
    """主函数"""
    args = parse_args()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        await run_demo()
    elif args.idea:
        await run_with_idea(
            args.idea,
            args.feishu_app_id,
            args.feishu_app_secret,
            args.llm_api_key
        )
    else:
        # 默认运行演示
        await run_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 程序已退出")
