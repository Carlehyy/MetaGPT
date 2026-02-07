"""
老板(Boss)角色实现
负责战略决策、资源分配和最终验收
"""
from typing import Optional, List, Dict, Any
from .base_role import BaseRole, Message, DiscussionContext


class Boss(BaseRole):
    """
    老板角色
    
    职责：
    - 审批产品需求和战略规划
    - 分配资源和预算
    - 对技术方案提供高层意见
    - 最终验收产品上线
    - 关注业务目标和ROI
    """
    
    def __init__(self):
        super().__init__(
            role_id="boss",
            name="老板",
            avatar="👔",
            description="公司老板/CEO，负责战略决策和资源分配"
        )
        self.decisions: List[Dict[str, Any]] = []
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是公司老板/CEO，负责战略决策和资源分配。

你的职责：
1. 审批产品需求和战略规划
2. 分配资源和预算
3. 对技术方案提供高层意见
4. 最终验收产品上线
5. 关注业务目标和ROI

工作风格：
- 关注宏观战略，不过度介入执行细节
- 审批关键节点：需求、技术方案、部署上线
- 提供资源支持和高层指导
- 对最终结果负责

回复原则：
- 简洁明了，直击要点
- 从战略高度给出意见
- 需要时做出明确决策"""
    
    async def make_decision(
        self,
        topic: str,
        options: List[str],
        context: DiscussionContext
    ) -> Dict[str, Any]:
        """
        做出决策
        
        Args:
            topic: 决策主题
            options: 可选方案
            context: 讨论上下文
            
        Returns:
            决策结果
        """
        prompt = f"""请就以下事项做出决策：

主题：{topic}
可选方案：
"""
        for i, option in enumerate(options, 1):
            prompt += f"{i}. {option}\n"
        
        prompt += """
请从战略高度评估各方案，考虑：
1. 与公司战略的契合度
2. 资源投入与回报
3. 风险与可行性
4. 长期价值

请给出你的决策和理由。"""
        
        response = await self.chat(prompt, context)
        
        decision = {
            "topic": topic,
            "options": options,
            "decision": response,
            "phase": context.phase,
            "timestamp": self.get_timestamp()
        }
        self.decisions.append(decision)
        
        return decision
    
    async def review_deliverable(
        self,
        deliverable_type: str,
        content: str,
        context: DiscussionContext
    ) -> Dict[str, Any]:
        """
        评审交付物
        
        Args:
            deliverable_type: 交付物类型
            content: 交付物内容
            context: 讨论上下文
            
        Returns:
            评审结果
        """
        prompt = f"""请评审以下交付物：

类型：{deliverable_type}
内容：
{content}

请从以下维度评审：
1. 是否符合公司战略方向
2. 是否满足业务需求
3. 质量和完整性
4. 风险和可行性

请输出评审结果（通过/不通过）和意见。"""
        
        response = await self.chat(prompt, context)
        
        return {
            "deliverable_type": deliverable_type,
            "phase": context.phase,
            "response": response
        }
    
    def get_decision_history(self) -> List[dict]:
        """获取决策历史"""
        return self.decisions.copy()
    
    def should_participate(self, phase: str) -> bool:
        """
        判断是否应该参与某阶段
        
        Args:
            phase: 阶段名称
            
        Returns:
            是否应该参与
        """
        # 老板需要参与的阶段
        boss_phases = [
            "requirement",  # 需求分析 - 咨询
            "architecture", # 技术方案 - 咨询
            "design",       # UI设计 - 知会
            "deployment",   # 部署上线 - 验收
            "operations"    # 运维监控 - 知会
        ]
        return phase in boss_phases
