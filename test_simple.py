#!/usr/bin/env python3
"""
AI Team - 简化功能测试
"""
import asyncio
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_discussion_engine():
    """测试讨论引擎"""
    logger.info("=" * 60)
    logger.info("测试讨论引擎")
    logger.info("=" * 60)

    from discussion import DiscussionEngine, DiscussionConfig
    from discussion.round_robin import Role

    # 创建参与者
    roles = [
        Role(id="pm", name="产品经理", description="负责产品规划"),
        Role(id="arch", name="架构师", description="负责技术架构"),
        Role(id="dev", name="开发工程师", description="负责开发实现")
    ]

    # 创建讨论引擎
    config = DiscussionConfig(max_rounds=5)
    engine = DiscussionEngine(
        roles=roles,
        config=config
    )

    logger.info(f"讨论引擎创建成功，角色数: {len(roles)}")
    logger.info("✅ 讨论引擎测试通过")
    return True


async def test_consensus_detector():
    """测试共识检测器"""
    logger.info("=" * 60)
    logger.info("测试共识检测器")
    logger.info("=" * 60)

    from discussion.consensus import ConsensusChecker, ConsensusStrategy

    checker = ConsensusChecker(strategy=ConsensusStrategy.HYBRID)
    logger.info("共识检测器创建成功")
    logger.info("✅ 共识检测器测试通过")
    return True


async def test_role_matrix():
    """测试职责矩阵"""
    logger.info("=" * 60)
    logger.info("测试职责矩阵")
    logger.info("=" * 60)

    from roles import RoleMatrix, ParticipationType

    matrix = RoleMatrix()
    logger.info(f"职责矩阵创建成功")
    logger.info("✅ 职责矩阵测试通过")
    return True


async def test_roles():
    """测试角色"""
    logger.info("=" * 60)
    logger.info("测试角色")
    logger.info("=" * 60)

    from roles import Boss, ProductManager, Architect, ProductDesigner

    logger.info("角色导入成功")
    logger.info("✅ 角色测试通过")
    return True


async def test_workflow_manager():
    """测试工作流管理器"""
    logger.info("=" * 60)
    logger.info("测试工作流管理器")
    logger.info("=" * 60)

    from company import WorkflowManager

    logger.info("工作流管理器导入成功")
    logger.info("✅ 工作流管理器测试通过")
    return True


async def test_agent_company():
    """测试AgentCompany主类"""
    logger.info("=" * 60)
    logger.info("测试AgentCompany主类")
    logger.info("=" * 60)

    from company import AgentCompany, CompanyConfig

    logger.info("AgentCompany导入成功")
    logger.info("✅ AgentCompany测试通过")
    return True


async def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始功能验证测试")
    logger.info("=" * 60)

    tests = [
        ("讨论引擎", test_discussion_engine),
        ("共识检测器", test_consensus_detector),
        ("职责矩阵", test_role_matrix),
        ("角色", test_roles),
        ("工作流管理器", test_workflow_manager),
        ("AgentCompany", test_agent_company),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ {name}测试失败: {str(e)}")
            results.append((name, False))

    # 总结
    logger.info("=" * 60)
    logger.info("测试结果总结")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {name}")

    logger.info(f"总计: {passed}/{total} 测试通过")
    logger.info("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

