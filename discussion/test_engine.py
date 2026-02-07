"""
讨论引擎测试文件

用于验证讨论引擎的各项功能
"""

import asyncio
import sys
sys.path.insert(0, '/mnt/okcomputer/output')

from discussion import (
    DiscussionEngine, Role, DiscussionConfig,
    DiscussionState, TurnOrderStrategy, ConsensusStrategy,
    Message, MessageType, MessagePriority
)


def test_basic_functionality():
    """测试基础功能"""
    print("=" * 60)
    print("测试1: 基础功能测试")
    print("=" * 60)
    
    # 创建角色
    roles = [
        Role(id="pm", name="产品经理", description="负责产品规划"),
        Role(id="tech", name="技术负责人", description="负责技术方案"),
        Role(id="boss", name="老板", description="最终决策者", is_boss=True)
    ]
    
    # 创建引擎
    config = DiscussionConfig(max_rounds=5)
    engine = DiscussionEngine(roles=roles, config=config, boss_role_id="boss")
    
    print(f"✓ 引擎创建成功")
    print(f"  - 角色数: {len(roles)}")
    print(f"  - 最大轮次: {config.max_rounds}")
    print(f"  - 初始状态: {engine.get_current_state()}")
    
    return True


def test_state_management():
    """测试状态管理"""
    print("\n" + "=" * 60)
    print("测试2: 状态管理测试")
    print("=" * 60)
    
    roles = [Role(id="r1", name="角色1")]
    engine = DiscussionEngine(roles=roles)
    
    # 测试状态转换
    assert engine.get_current_state() == DiscussionState.PENDING
    print(f"✓ 初始状态: {engine.get_current_state()}")
    
    # 测试暂停/恢复
    engine.state_manager.transition_to(DiscussionState.ONGOING)
    assert engine.state_manager.is_active() == True
    print(f"✓ 活跃状态检测正常")
    
    engine.state_manager.transition_to(DiscussionState.CONSENSUS_REACHED)
    assert engine.state_manager.is_terminal() == True
    print(f"✓ 终止状态检测正常")
    
    return True


def test_round_robin():
    """测试轮流发言"""
    print("\n" + "=" * 60)
    print("测试3: 轮流发言测试")
    print("=" * 60)
    
    roles = [
        Role(id="r1", name="角色1"),
        Role(id="r2", name="角色2"),
        Role(id="r3", name="角色3")
    ]
    
    from discussion.round_robin import TurnManager, TurnOrderStrategy
    
    # 测试固定顺序
    manager = TurnManager(roles, TurnOrderStrategy.FIXED)
    order = manager.get_speaking_order()
    print(f"✓ 固定顺序: {order}")
    
    # 测试轮询
    speaker1 = manager.get_next_speaker()
    print(f"✓ 第一个发言者: {speaker1.name}")
    
    manager.mark_spoken(speaker1.id)
    speaker2 = manager.get_next_speaker()
    print(f"✓ 第二个发言者: {speaker2.name}")
    
    manager.mark_spoken(speaker2.id)
    speaker3 = manager.get_next_speaker()
    print(f"✓ 第三个发言者: {speaker3.name}")
    
    # 测试轮次完成
    manager.mark_spoken(speaker3.id)
    assert manager.is_round_complete() == True
    print(f"✓ 轮次完成检测正常")
    
    return True


def test_consensus_detection():
    """测试共识检测"""
    print("\n" + "=" * 60)
    print("测试4: 共识检测测试")
    print("=" * 60)
    
    from discussion.consensus import (
        KeywordConsensusDetector,
        SimilarityConsensusDetector,
        HybridConsensusDetector
    )
    
    # 测试关键词检测
    detector = KeywordConsensusDetector(threshold=0.7)
    messages = ["我同意", "赞成", "支持这个方案", "没问题"]
    participants = ["r1", "r2", "r3", "r4"]
    
    result = detector.detect(messages, participants)
    print(f"✓ 关键词检测: reached={result.reached}, confidence={result.confidence:.2%}")
    
    # 测试相似度检测
    detector2 = SimilarityConsensusDetector(similarity_threshold=0.5)
    messages2 = ["方案很好", "这个方案不错", "同意方案", "支持"]
    
    result2 = detector2.detect(messages2, participants)
    print(f"✓ 相似度检测: reached={result2.reached}, confidence={result2.confidence:.2%}")
    
    # 测试混合检测
    detector3 = HybridConsensusDetector()
    messages3 = ["同意", "赞成", "支持", "没问题"]
    
    result3 = detector3.detect(messages3, participants, current_round=3)
    print(f"✓ 混合检测: reached={result3.reached}, confidence={result3.confidence:.2%}")
    print(f"  原因: {result3.reason}")
    
    return True


def test_message_store():
    """测试消息存储"""
    print("\n" + "=" * 60)
    print("测试5: 消息存储测试")
    print("=" * 60)
    
    from discussion.message import MessageStore, MessageType
    
    store = MessageStore()
    
    # 添加消息
    for i in range(5):
        msg = Message(
            content=f"消息内容{i}",
            sender_id=f"role{i % 2 + 1}",
            sender_name=f"角色{i % 2 + 1}",
            round_number=i // 2 + 1,
            message_type=MessageType.SPEECH
        )
        store.add(msg)
    
    print(f"✓ 添加了5条消息")
    print(f"  - 总消息数: {store.get_message_count()}")
    print(f"  - 参与者数: {len(store.get_participants())}")
    print(f"  - 轮次数: {store.get_round_count()}")
    
    # 测试查询
    round1_msgs = store.get_by_round(1)
    print(f"✓ 第1轮消息数: {len(round1_msgs)}")
    
    role1_msgs = store.get_by_sender("role1")
    print(f"✓ 角色1消息数: {len(role1_msgs)}")
    
    recent = store.get_recent(3)
    print(f"✓ 最近3条消息获取成功")
    
    return True


def test_boss_intervention():
    """测试老板介入检测"""
    print("\n" + "=" * 60)
    print("测试6: 老板介入检测测试")
    print("=" * 60)
    
    roles = [
        Role(id="pm", name="产品经理"),
        Role(id="boss", name="老板", is_boss=True)
    ]
    
    engine = DiscussionEngine(roles=roles, boss_role_id="boss")
    
    # 测试普通消息
    normal_msg = Message(
        content="我认为这个方案可行",
        sender_id="pm",
        sender_name="产品经理"
    )
    assert engine.check_boss_intervention(normal_msg) == False
    print(f"✓ 普通消息检测正常")
    
    # 测试老板角色消息
    boss_msg = Message(
        content="大家继续讨论",
        sender_id="boss",
        sender_name="老板"
    )
    assert engine.check_boss_intervention(boss_msg) == True
    print(f"✓ 老板角色消息检测正常")
    
    # 测试关键词触发
    decision_msg = Message(
        content="我决定采用方案A",
        sender_id="pm",
        sender_name="产品经理"
    )
    assert engine.check_boss_intervention(decision_msg) == True
    print(f"✓ 决策关键词检测正常")
    
    return True


async def test_full_discussion():
    """测试完整讨论流程"""
    print("\n" + "=" * 60)
    print("测试7: 完整讨论流程测试")
    print("=" * 60)
    
    roles = [
        Role(id="pm", name="产品经理", priority=1),
        Role(id="tech", name="技术负责人", priority=2),
        Role(id="design", name="设计师", priority=3)
    ]
    
    config = DiscussionConfig(
        max_rounds=3,
        consensus_strategy=ConsensusStrategy.HYBRID,
        auto_check_consensus=True
    )
    
    engine = DiscussionEngine(roles=roles, config=config)
    
    # 设置回调
    consensus_triggered = [False]
    def on_consensus(result):
        consensus_triggered[0] = True
        print(f"  [回调] 达成共识！置信度: {result.confidence:.2%}")
    
    engine.on_consensus(on_consensus)
    
    # 开始讨论
    success = await engine.start_discussion("测试主题")
    assert success == True
    print(f"✓ 讨论开始成功")
    
    # 模拟讨论
    message_count = 0
    while engine.get_current_state() == DiscussionState.ONGOING and message_count < 10:
        msg_request = await engine.next_turn()
        if msg_request is None:
            break
        
        # 模拟发言
        responses = {
            "pm": "我认为应该优先实现核心功能",
            "tech": "技术上可行，同意",
            "design": "从设计角度支持这个方案"
        }
        msg_request.content = responses.get(msg_request.sender_id, "继续讨论")
        
        engine.submit_message(msg_request)
        message_count += 1
        
        print(f"  [{msg_request.round_number}] {msg_request.sender_name}: {msg_request.content[:20]}...")
    
    print(f"✓ 讨论完成，共 {message_count} 条消息")
    print(f"✓ 最终状态: {engine.get_current_state()}")
    
    # 获取进度
    progress = engine.get_progress()
    print(f"  - 当前轮次: {progress['current_round']}")
    print(f"  - 消息总数: {progress['message_count']}")
    print(f"  - 进度: {progress['progress_percentage']:.1f}%")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("讨论引擎测试套件")
    print("=" * 60)
    
    tests = [
        ("基础功能", test_basic_functionality),
        ("状态管理", test_state_management),
        ("轮流发言", test_round_robin),
        ("共识检测", test_consensus_detection),
        ("消息存储", test_message_store),
        ("老板介入", test_boss_intervention),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✓ {name}测试通过")
        except Exception as e:
            failed += 1
            print(f"✗ {name}测试失败: {e}")
    
    # 异步测试
    try:
        asyncio.run(test_full_discussion())
        passed += 1
        print(f"✓ 完整流程测试通过")
    except Exception as e:
        failed += 1
        print(f"✗ 完整流程测试失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}, 失败 {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
