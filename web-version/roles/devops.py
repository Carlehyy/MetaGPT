"""
运维工程师角色 - 部署上线、运维监控

作为运维负责人，运维工程师负责：
- 部署方案制定
- 环境配置管理
- 上线部署执行
- 系统监控
- 故障处理
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class DevOps(BaseRole):
    """
    运维工程师角色
    
    职责：
    - 制定部署方案
    - 管理环境配置
    - 执行上线部署
    - 配置系统监控
    - 处理线上故障
    - 优化系统性能
    """
    
    def __init__(self, name: str = "运维工程师", **kwargs):
        """
        初始化运维工程师角色
        
        Args:
            name: 角色名称，默认为"运维工程师"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="DevOps工程师",
            responsibilities=[
                "制定部署方案",
                "管理环境配置",
                "执行上线部署",
                "配置系统监控",
                "处理线上故障",
                "优化系统性能",
                "管理CI/CD流程",
                "保障系统稳定性"
            ],
            expertise=[
                "Linux系统管理",
                "容器技术(Docker/Kubernetes)",
                "云平台(AWS/Azure/阿里云)",
                "CI/CD工具(Jenkins/GitLab CI)",
                "配置管理(Ansible/Terraform)",
                "监控工具(Prometheus/Grafana)",
                "日志管理(ELK/Loki)",
                "网络安全",
                "Shell/Python脚本"
            ],
            communication_style="""
严谨可靠、注重细节，对系统稳定性有高要求。
善于发现和解决系统问题。
能够清晰地描述部署和运维方案。
""",
            decision_scope="""
运维相关的决策：
- 部署方案
- 环境配置
- 监控策略
- 扩容方案
- 故障处理方案

需要@老板的情况：
- 发生重大故障
- 需要重大架构调整
- 成本超出预算
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.DEVOPS.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 部署记录
        self.deployments: List[Dict[str, Any]] = []
        # 监控配置
        self.monitoring_configs: List[Dict[str, Any]] = []
        # 故障记录
        self.incidents: List[Dict[str, Any]] = []
    
    async def participate(
        self,
        context: DiscussionContext,
        topic: str,
        previous_messages: List[Message]
    ) -> str:
        """
        参与讨论
        
        Args:
            context: 讨论上下文
            topic: 讨论主题
            previous_messages: 之前的消息列表
            
        Returns:
            运维工程师的发言内容
        """
        prompt = self._build_participation_prompt(context, topic, previous_messages)
        response = await self.chat(prompt, context)
        return response
    
    def _build_participation_prompt(
        self,
        context: DiscussionContext,
        topic: str,
        previous_messages: List[Message]
    ) -> str:
        """构建参与讨论的提示"""
        prompt = f"""当前阶段: {context.phase}
讨论主题: {topic}

你作为运维工程师，需要从运维角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P8_DEPLOYMENT:
            prompt += """
请从以下角度分析：
1. 部署方案的可行性
2. 环境准备情况
3. 风险评估
4. 回滚方案
"""
        elif phase == Phase.P9_OPERATION_MONITORING:
            prompt += """
请从以下角度分析：
1. 系统运行状态
2. 监控告警分析
3. 性能指标
4. 优化建议
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        运维工程师在以下情况可以做出决策：
        1. 部署相关的决策
        2. 运维监控相关的决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.DEVOPS)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def create_deployment_script(
        self,
        context: DiscussionContext,
        application_info: str
    ) -> Dict[str, Any]:
        """
        创建部署脚本
        
        Args:
            context: 讨论上下文
            application_info: 应用信息
            
        Returns:
            部署脚本
        """
        prompt = f"""请为以下应用创建部署脚本：

应用信息:
{application_info}

部署脚本应包含：
1. 环境检查
2. 依赖安装
3. 配置文件准备
4. 应用部署
5. 健康检查
6. 回滚逻辑

请提供Shell或Python部署脚本。
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "application_info": application_info,
            "phase": context.phase,
            "type": "deployment_script"
        }
    
    async def setup_monitoring(
        self,
        context: DiscussionContext,
        system_info: str
    ) -> Dict[str, Any]:
        """
        设置监控
        
        Args:
            context: 讨论上下文
            system_info: 系统信息
            
        Returns:
            监控配置
        """
        prompt = f"""请为以下系统设置监控：

系统信息:
{system_info}

监控配置应包含：
1. 监控指标（CPU、内存、磁盘、网络等）
2. 应用性能指标（QPS、延迟、错误率等）
3. 告警规则
4. 告警通知方式
5. 监控面板配置

请以JSON格式输出监控配置：
{{
    "metrics": ["指标1", "指标2"],
    "alerts": [
        {{
            "name": "告警名称",
            "condition": "告警条件",
            "severity": "严重程度",
            "notification": "通知方式"
        }}
    ],
    "dashboards": ["面板1", "面板2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        monitoring_config = {
            "content": response,
            "system_info": system_info,
            "phase": context.phase
        }
        self.monitoring_configs.append(monitoring_config)
        
        return monitoring_config
    
    async def handle_incident(
        self,
        context: DiscussionContext,
        incident_description: str
    ) -> Dict[str, Any]:
        """
        处理故障
        
        Args:
            context: 讨论上下文
            incident_description: 故障描述
            
        Returns:
            故障处理方案
        """
        prompt = f"""请处理以下故障：

故障描述:
{incident_description}

请提供：
1. 故障影响评估
2. 根因分析
3. 临时解决方案
4. 永久解决方案
5. 预防措施
6. 复盘总结

请以Markdown格式输出故障处理报告。
"""
        
        response = await self.chat(prompt, context)
        
        incident = {
            "content": response,
            "description": incident_description,
            "phase": context.phase,
            "status": "resolved"
        }
        self.incidents.append(incident)
        
        return incident
    
    async def create_ci_cd_pipeline(
        self,
        context: DiscussionContext,
        project_info: str
    ) -> Dict[str, Any]:
        """
        创建CI/CD流水线
        
        Args:
            context: 讨论上下文
            project_info: 项目信息
            
        Returns:
            CI/CD配置
        """
        prompt = f"""请为以下项目创建CI/CD流水线配置：

项目信息:
{project_info}

CI/CD流水线应包含：
1. 代码构建
2. 单元测试
3. 代码质量检查
4. 镜像构建
5. 部署到测试环境
6. 集成测试
7. 部署到生产环境

请提供Jenkinsfile、GitLab CI配置或GitHub Actions配置。
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "project_info": project_info,
            "phase": context.phase,
            "type": "ci_cd_config"
        }
    
    async def generate_ops_report(
        self,
        context: DiscussionContext,
        monitoring_data: str
    ) -> Dict[str, Any]:
        """
        生成运维报告
        
        Args:
            context: 讨论上下文
            monitoring_data: 监控数据
            
        Returns:
            运维报告
        """
        prompt = f"""请根据以下监控数据生成运维报告：

监控数据:
{monitoring_data}

运维报告应包含：
1. 系统运行概况
2. 性能指标分析
3. 可用性统计
4. 告警分析
5. 问题记录
6. 优化建议

请以Markdown格式输出运维报告。
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "monitoring_data": monitoring_data,
            "phase": context.phase,
            "type": "ops_report"
        }
    
    def get_deployments(self) -> List[Dict[str, Any]]:
        """获取所有部署记录"""
        return self.deployments.copy()
    
    def get_monitoring_configs(self) -> List[Dict[str, Any]]:
        """获取所有监控配置"""
        return self.monitoring_configs.copy()
    
    def get_incidents(self) -> List[Dict[str, Any]]:
        """获取所有故障记录"""
        return self.incidents.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.DEVOPS.value, DevOps)


if __name__ == "__main__":
    import asyncio
    
    async def test_devops():
        devops = DevOps()
        print(f"创建角色: {devops}")
        print(f"系统提示词长度: {len(devops.system_prompt)}")
    
    asyncio.run(test_devops())
