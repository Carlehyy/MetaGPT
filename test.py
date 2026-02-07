#!/usr/bin/env python3
"""
AI Team - 功能测试脚本

验证核心功能模块。
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

    from discussion import DiscussionEngine, DiscussionConfig, DiscussionState
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

    # 注册回调
    messages_received = []
    states_received = []

    engine.on_consensus(lambda msg: messages_received.append(msg))
    engine.on_state_change(lambda old, new: states_received.append(new))

    # 开始讨论
    logger.info("开始讨论...")
    await engine.start_discussion("开发一个待办事项应用")

    # 模拟发言
    test_messages = [
        ("产品经理", "需求很明确，我们需要一个支持语音输入的待办应用"),
        ("架构师", "技术上可以使用React Native实现跨平台"),
        ("开发工程师", "没问题，我可以负责前端开发"),
        ("产品经理", "大家意见一致，我们就按这个方案执行"),
        ("架构师", "同意"),
        ("开发工程师", "同意")
    ]

    for sender, content in test_messages:
        next_speaker = await engine.next_turn()
        if next_speaker:
            logger.info(f"[{sender}] {content[:40]}...")
            await engine.submit_message(sender, content)

    # 检查结果
    logger.info(f"讨论状态: {engine.state.state.value}")
    logger.info(f"消息数量: {len(engine.messages)}")
    logger.info(f"当前轮数: {engine.state.current_round}")

    summary = engine.get_discussion_summary()
    logger.info(f"摘要: {summary}")

    # 验证
    assert len(engine.messages) > 0, "应该有消息记录"

    logger.info("讨论引擎测试通过")
    return True





async def test_consensus_detector():
    """测试共识检测器"""
    logger.info("=" * 60)
    logger.info("测试共识检测器")
    logger.info("=" * 60)
    
    from discussion.consensus import ConsensusChecker, ConsensusStrategy
    
    detector = ConsensusChecker(strategy=ConsensusStrategy.HYBRID)
    
    # 测试显式同意
    messages = [
        {"sender": "A", "content": "我同意这个方案", "round_num": 1},
        {"sender": "B", "content": "我也同意", "round_num": 1},
        {"sender": "C", "content": "达成共识", "round_num": 1}
    ]
    
    reached, reason = detector.check_consensus(messages, ["A", "B", "C"], 1)
    logger.info(f"显式同意检测: {reached}, {reason}")
    assert reached, "应该检测到共识"
    
    # 测试Pass比例
    messages = [
        {"sender": "A", "content": "pass", "round_num": 1, "msg_type": "pass"},
        {"sender": "B", "content": "跳过", "round_num": 1, "msg_type": "pass"},
        {"sender": "C", "content": "无意见", "round_num": 1, "msg_type": "pass"}
    ]
    
    reached, reason = detector.check_consensus(messages, ["A", "B", "C"], 1)
    logger.info(f"Pass比例检测: {reached}, {reason}")
    assert reached, "应该检测到共识"
    
    logger.info("✅ 共识检测器测试通过\n")
    return True


async def test_role_matrix():
    """测试职责矩阵"""
    logger.info("=" * 60)
    logger.info("测试职责矩阵")
    logger.info("=" * 60)
    
    from roles import RoleMatrix, ParticipationType
    
    # 测试获取参与类型
    ptype = RoleMatrix.get_participation("P1", "产品经理")
    logger.info(f"P1阶段产品经理参与类型: {ptype.value}")
    assert ptype == ParticipationType.LEAD, "产品经理应该负责P1"
    
    # 测试获取参与者
    participants = RoleMatrix.get_phase_participants("P1")
    logger.info(f"P1阶段参与者: {participants}")
    assert "产品经理" in participants, "产品经理应该参与P1"
    
    # 测试获取负责人
    leader = RoleMatrix.get_phase_leader("P1")
    logger.info(f"P1阶段负责人: {leader}")
    assert leader == "产品经理", "产品经理应该是P1负责人"
    
    logger.info("✅ 职责矩阵测试通过\n")
    return True


async def test_roles():
    """测试角色"""
    logger.info("=" * 60)
    logger.info("测试角色")
    logger.info("=" * 60)
    
    from roles import Boss, ProductManager, Architect, ProductDesigner
    from roles import ProjectManager, Engineer, QAEngineer, DevOps
    
    # 测试老板
    boss = Boss()
    logger.info(f"老板: {boss.name}, {boss.avatar}")
    assert boss.name == "老板"
    
    # 测试产品经理
    pm = ProductManager()
    logger.info(f"产品经理: {pm.name}, {pm.avatar}")
    assert pm.name == "产品经理"
    
    # 测试架构师
    architect = Architect()
    logger.info(f"架构师: {architect.name}, {architect.avatar}")
    assert architect.name == "架构师"
    
    # 测试产品设计师
    designer = ProductDesigner()
    logger.info(f"产品设计师: {designer.name}, {designer.avatar}")
    assert designer.name == "产品设计师"
    
    # 测试项目经理
    project_manager = ProjectManager()
    logger.info(f"项目经理: {project_manager.name}, {project_manager.avatar}")
    assert project_manager.name == "项目经理"
    
    # 测试开发工程师
    engineer = Engineer()
    logger.info(f"开发工程师: {engineer.name}, {engineer.avatar}")
    assert engineer.name == "开发工程师"
    
    # 测试测试工程师
    qa = QAEngineer()
    logger.info(f"测试工程师: {qa.name}, {qa.avatar}")
    assert qa.name == "测试工程师"
    
    # 测试运维工程师
    devops = DevOps()
    logger.info(f"运维工程师: {devops.name}, {devops.avatar}")
    assert devops.name == "运维工程师"
    
    logger.info("✅ 角色测试通过\n")
    return True


async def test_workflow_manager():
    """测试工作流管理器"""
    logger.info("=" * 60)
    logger.info("测试工作流管理器")
    logger.info("=" * 60)
    
    from company import WorkflowManager
    
    workflow = WorkflowManager()
    
    # 检查阶段定义
    assert len(workflow.PHASES) == 9, "应该有9个阶段"
    logger.info(f"✅ 定义了 {len(workflow.PHASES)} 个阶段")
    
    # 检查阶段信息
    phase = workflow.get_current_phase()
    logger.info(f"当前阶段: {phase}")
    
    # 检查进度
    progress = workflow.get_phase_progress()
    logger.info(f"进度: {progress}")
    
    logger.info("✅ 工作流管理器测试通过\n")
    return True


async def test_agent_company():
    """测试AgentCompany主类"""
    logger.info("=" * 60)
    logger.info("测试AgentCompany主类")
    logger.info("=" * 60)
    
    from company import AgentCompany, CompanyConfig
    
    config = CompanyConfig(
        llm_api_key="test_key",
        feishu_app_id="test_app_id",
        feishu_app_secret="test_app_secret"
    )
    
    company = AgentCompany(config)
    
    # 检查角色定义
    assert len(company.ROLES) == 8, "应该有8个角色"
    logger.info(f"✅ 定义了 {len(company.ROLES)} 个角色")
    
    # 检查阶段定义
    assert len(company.PHASES) == 9, "应该有9个阶段"
    logger.info(f"✅ 定义了 {len(company.PHASES)} 个阶段")
    
    # 检查飞书机器人
    assert company.feishu_bot is not None, "应该有飞书机器人实例"
    logger.info("✅ 飞书机器人已初始化")
    
    await company.close()
    
    logger.info("✅ AgentCompany测试通过\n")
    return True


async def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "=" * 60)
    logger.info("开始功能验证测试")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("讨论引擎", test_discussion_engine),
        ("共识检测器", test_consensus_detector),
        ("职责矩阵", test_role_matrix),
        ("角色", test_roles),
        ("工作流管理器", test_workflow_manager),
        ("AgentCompany", test_agent_company)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ {name}测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    logger.info("\n" + "=" * 60)
    logger.info("测试结果总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    logger.info("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("测试已中断")
        sys.exit(1)
