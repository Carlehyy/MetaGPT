"""
AI虚拟软件公司 - 使用示例

演示如何创建项目并运行完整的9阶段软件开发流程
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_single_phase():
    """示例：运行单个阶段讨论"""
    print("=" * 60)
    print("示例：运行单个阶段讨论")
    print("=" * 60)
    
    from roles import (
        Boss, ProductManager, Architect,
        Phase, Role, get_participation_type
    )
    from discussion import DiscussionEngine
    
    # 创建讨论引擎
    engine = DiscussionEngine(max_rounds=3)
    
    # 创建角色
    boss = Boss()
    pm = ProductManager()
    architect = Architect()
    
    # 注册角色
    engine.register_roles([boss, pm, architect])
    
    # 定义阶段和主题
    phase = Phase.P1_REQUIREMENT_ANALYSIS
    topic = "电商APP订单功能需求分析"
    initial_message = """我们需要开发一个电商APP的订单功能。

用户需求：
1. 用户可以浏览商品并添加到购物车
2. 用户可以提交订单
3. 支持多种支付方式
4. 用户可以查看订单状态
5. 支持订单取消和退款

请进行需求分析，输出PRD文档。"""
    
    print(f"\n阶段: {phase.value}")
    print(f"主题: {topic}")
    print(f"参与角色: Boss, ProductManager, Architect")
    
    # 运行讨论
    result = await engine.start_discussion(
        phase=phase,
        topic=topic,
        initial_message=initial_message
    )
    
    print(f"\n讨论结果:")
    print(f"状态: {result.status.value}")
    print(f"消息数量: {len(result.messages)}")
    
    if result.summary:
        print(f"\n总结:\n{result.summary}")
    
    return result


async def example_full_project():
    """示例：运行完整项目"""
    print("\n" + "=" * 60)
    print("示例：运行完整项目")
    print("=" * 60)
    
    from company import AgentCompany
    
    # 创建公司
    company = AgentCompany(
        max_discussion_rounds=5,
        enable_websocket=False  # 禁用WebSocket以简化示例
    )
    
    # 创建项目
    project = await company.create_project(
        project_id=f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name="智能客服系统",
        description="""开发一个基于AI的智能客服系统，具备以下功能：
1. 自然语言理解，识别用户意图
2. 智能问答，自动回复常见问题
3. 人工客服转接
4. 对话记录和分析
5. 多渠道接入（Web、APP、微信）"""
    )
    
    print(f"\n项目创建成功:")
    print(f"ID: {project.id}")
    print(f"名称: {project.name}")
    print(f"描述: {project.description[:100]}...")
    
    # 添加事件监听器
    def on_phase_start(phase):
        print(f"\n[事件] 阶段开始: {phase.value}")
    
    def on_phase_end(result):
        print(f"[事件] 阶段结束: {result.phase.value}, 状态: {result.status}")
    
    def on_message(msg):
        if msg.sender:
            print(f"[{msg.sender}] {msg.content[:80]}...")
    
    company.add_event_listener("phase_start", on_phase_start)
    company.add_event_listener("phase_end", on_phase_end)
    company.add_event_listener("message", on_message)
    
    # 启动项目
    print("\n开始执行项目...")
    # 注意：实际运行需要调用LLM，这里仅展示结构
    # results = await company.start_project(project)
    
    print("\n项目结构已创建，实际运行需要配置LLM API")
    
    return company


async def example_role_matrix():
    """示例：展示职责矩阵"""
    print("\n" + "=" * 60)
    print("示例：职责矩阵")
    print("=" * 60)
    
    from roles import (
        Phase, Role, get_participation_type,
        get_responsible_roles, get_consult_roles,
        get_phase_description, print_matrix
    )
    
    # 打印完整矩阵
    print_matrix()
    
    # 展示P1阶段的参与情况
    print("\n\nP1阶段参与情况:")
    for role in Role:
        ptype = get_participation_type(Phase.P1_REQUIREMENT_ANALYSIS, role)
        print(f"  {role.value}: {ptype.value}")
    
    # 展示各阶段的负责角色
    print("\n各阶段负责角色:")
    for phase in Phase:
        responsible = get_responsible_roles(phase)
        print(f"  {phase.value}: {[r.value for r in responsible]}")


async def example_role_creation():
    """示例：创建和使用角色"""
    print("\n" + "=" * 60)
    print("示例：创建和使用角色")
    print("=" * 60)
    
    from roles import (
        RoleFactory, Boss, ProductManager, Architect,
        ProductDesigner, ProjectManager, Engineer,
        QAEngineer, DevOps
    )
    
    # 创建所有角色
    roles = {
        "老板": Boss(name="张总"),
        "产品经理": ProductManager(name="李产品经理"),
        "架构师": Architect(name="王架构师"),
        "产品设计师": ProductDesigner(name="赵设计师"),
        "项目经理": ProjectManager(name="刘项目经理"),
        "开发工程师": Engineer(name="陈工程师"),
        "测试工程师": QAEngineer(name="杨测试"),
        "运维工程师": DevOps(name="周运维"),
    }
    
    print("\n已创建角色:")
    for name, role in roles.items():
        print(f"  {name}: {role.name} ({role.role_type})")
    
    # 使用RoleFactory创建角色
    print("\n使用RoleFactory创建角色:")
    pm = RoleFactory.create("产品经理", name="Factory创建的产品经理")
    print(f"  创建: {pm}")
    
    # 列出所有注册的角色类型
    print(f"\n注册的角色类型: {RoleFactory.list_roles()}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI虚拟软件公司 - 使用示例")
    print("=" * 60)
    
    # 运行示例
    await example_role_matrix()
    await example_role_creation()
    # await example_single_phase()  # 需要LLM API
    await example_full_project()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
