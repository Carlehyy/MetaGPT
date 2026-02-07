"""
Agent Company - 公司主类
=======================
整合所有组件，提供统一的对外接口
"""

import asyncio
import json
import os
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

import yaml

# 导入架构模块
from architecture.base import DiscussionConfig, PhaseConfig, PhaseStatus
from architecture.phase import Phase, PhaseManager
from architecture.role import Role, BossRole, create_all_roles
from architecture.message import DiscussionMessage
from architecture.discussion_engine import DiscussionEngine, DiscussionState

# 导入飞书模块
from feishu.bot import FeishuBot, FeishuConfig

# 导入工作流模块
from .workflow import WorkflowManager, PhaseExecutor, PhaseResult, PhaseResultStatus

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """项目状态"""
    IDLE = "idle"                    # 空闲
    WAITING_FOR_IDEA = "waiting_for_idea"  # 等待需求输入
    RUNNING = "running"              # 运行中
    PAUSED = "paused"                # 暂停
    COMPLETED = "completed"          # 完成
    ERROR = "error"                  # 错误


@dataclass
class CompanyConfig:
    """公司配置"""
    # LLM配置
    llm_api_key: str = ""
    llm_model: str = "glm-4"
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # 飞书配置
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    
    # 讨论配置
    max_rounds_per_phase: int = 20
    consensus_threshold: float = 0.8
    
    # 数据目录
    data_dir: str = "./data"
    output_dir: str = "./outputs"
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'CompanyConfig':
        """从YAML文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return cls(
            llm_api_key=config.get('llm', {}).get('api_key', ''),
            llm_model=config.get('llm', {}).get('model', 'glm-4'),
            llm_base_url=config.get('llm', {}).get('base_url', ''),
            feishu_app_id=config.get('feishu', {}).get('app_id', ''),
            feishu_app_secret=config.get('feishu', {}).get('app_secret', ''),
            max_rounds_per_phase=config.get('discussion', {}).get('max_rounds_per_phase', 20),
            consensus_threshold=config.get('discussion', {}).get('consensus_threshold', 0.8),
            data_dir=config.get('app', {}).get('data_dir', './data'),
            output_dir=config.get('app', {}).get('output_dir', './outputs')
        )


class AgentCompany:
    """
    Agent Company - AI驱动的虚拟软件公司
    
    主要职责：
    1. 初始化所有组件（角色、阶段、讨论引擎、飞书机器人）
    2. 接收项目需求，启动9阶段流程
    3. 协调各阶段执行
    4. 与飞书集成，发送讨论过程
    5. 管理项目状态
    """
    
    def __init__(self, config: CompanyConfig):
        self.config = config
        self.status = ProjectStatus.IDLE
        
        # 创建目录
        os.makedirs(config.data_dir, exist_ok=True)
        os.makedirs(config.output_dir, exist_ok=True)
        
        # 初始化组件
        self._init_roles()
        self._init_phases()
        self._init_discussion_engine()
        self._init_feishu_bot()
        self._init_workflow()
        
        # 项目状态
        self.current_project: Optional[str] = None
        self.current_idea: Optional[str] = None
        self.phase_results: Dict[str, PhaseResult] = {}
        
        # 回调函数
        self._on_status_change: Optional[Callable[[ProjectStatus, ProjectStatus], None]] = None
        
        logger.info("Agent Company 初始化完成")
    
    def _init_roles(self):
        """初始化角色"""
        self.roles = create_all_roles()
        self.role_map = {r.role_id: r for r in self.roles}
        
        # 找到老板角色
        self.boss_role = None
        for role in self.roles:
            if isinstance(role, BossRole):
                self.boss_role = role
                break
        
        logger.info(f"已初始化 {len(self.roles)} 个角色")
    
    def _init_phases(self):
        """初始化阶段"""
        self.phase_manager = PhaseManager()
        logger.info(f"已初始化 {len(self.phase_manager.get_all_phases())} 个阶段")
    
    def _init_discussion_engine(self):
        """初始化讨论引擎"""
        discussion_config = DiscussionConfig(
            max_rounds_per_phase=self.config.max_rounds_per_phase,
            consensus_threshold=self.config.consensus_threshold
        )
        
        self.discussion_engine = DiscussionEngine(discussion_config)
        self.discussion_engine.register_roles(self.roles)
        
        logger.info("讨论引擎初始化完成")
    
    def _init_feishu_bot(self):
        """初始化飞书机器人"""
        if not self.config.feishu_app_id or not self.config.feishu_app_secret:
            logger.warning("飞书配置不完整，跳过飞书机器人初始化")
            self.feishu_bot = None
            return
        
        feishu_config = FeishuConfig(
            app_id=self.config.feishu_app_id,
            app_secret=self.config.feishu_app_secret
        )
        
        self.feishu_bot = FeishuBot(feishu_config)
        self.discussion_engine.register_feishu_bot(self.feishu_bot)
        
        logger.info("飞书机器人初始化完成")
    
    def _init_workflow(self):
        """初始化工作流管理器"""
        self.workflow_manager = WorkflowManager(
            phase_manager=self.phase_manager,
            roles=self.roles,
            discussion_engine=self.discussion_engine,
            on_phase_start=self._on_phase_start,
            on_phase_end=self._on_phase_end,
            on_message=self._on_discussion_message
        )
        
        logger.info("工作流管理器初始化完成")
    
    # ============ 状态管理 ============
    
    def _set_status(self, new_status: ProjectStatus):
        """设置状态"""
        old_status = self.status
        self.status = new_status
        
        logger.info(f"状态变更: {old_status.value} -> {new_status.value}")
        
        if self._on_status_change:
            try:
                self._on_status_change(old_status, new_status)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {e}")
    
    def on_status_change(self, callback: Callable[[ProjectStatus, ProjectStatus], None]):
        """设置状态变更回调"""
        self._on_status_change = callback
    
    # ============ 项目操作 ============
    
    async def start_project(self, idea: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        启动新项目
        
        Args:
            idea: 项目需求/想法
            project_name: 项目名称（可选）
            
        Returns:
            项目启动结果
        """
        if self.status == ProjectStatus.RUNNING:
            return {
                "success": False,
                "error": "已有项目正在运行"
            }
        
        self.current_idea = idea
        self.current_project = project_name or f"Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.phase_results = {}
        
        logger.info(f"启动新项目: {self.current_project}")
        
        # 发送启动通知
        await self._send_feishu_notification(
            f"🚀 新项目启动\n"
            f"名称: {self.current_project}\n"
            f"需求: {idea[:200]}..."
        )
        
        # 设置状态
        self._set_status(ProjectStatus.RUNNING)
        
        # 启动工作流
        try:
            self.phase_results = await self.workflow_manager.run_full_workflow(idea)
            
            # 项目完成
            self._set_status(ProjectStatus.COMPLETED)
            
            # 发送完成通知
            await self._send_feishu_notification(
                f"🎉 项目完成！\n"
                f"名称: {self.current_project}\n"
                f"完成阶段数: {len(self.phase_results)}"
            )
            
            # 保存结果
            self._save_project_results()
            
            return {
                "success": True,
                "project": self.current_project,
                "phases_completed": len(self.phase_results),
                "results": {k: v.to_dict() for k, v in self.phase_results.items()}
            }
            
        except Exception as e:
            logger.error(f"项目执行失败: {e}")
            self._set_status(ProjectStatus.ERROR)
            
            await self._send_feishu_notification(
                f"❌ 项目执行失败\n"
                f"错误: {str(e)}"
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_single_phase(self, phase_id: str, context: str = "") -> PhaseResult:
        """
        运行单个阶段
        
        Args:
            phase_id: 阶段ID (P1-P9)
            context: 上下文
            
        Returns:
            阶段执行结果
        """
        return await self.workflow_manager.run_single_phase(phase_id, context)
    
    def stop_project(self):
        """停止当前项目"""
        self.workflow_manager.stop()
        self._set_status(ProjectStatus.IDLE)
        logger.info("项目已停止")
    
    def pause_project(self):
        """暂停当前项目"""
        self._set_status(ProjectStatus.PAUSED)
        logger.info("项目已暂停")
    
    def resume_project(self):
        """恢复当前项目"""
        self._set_status(ProjectStatus.RUNNING)
        logger.info("项目已恢复")
    
    # ============ 回调处理 ============
    
    async def _on_phase_start(self, phase_id: str, phase_name: str):
        """阶段开始回调"""
        logger.info(f"阶段开始: {phase_name} ({phase_id})")
        
        # 发送飞书通知
        await self._send_feishu_notification(
            f"📋 阶段开始: {phase_name}\n"
            f"项目: {self.current_project}"
        )
    
    async def _on_phase_end(self, phase_id: str, result: PhaseResult):
        """阶段结束回调"""
        logger.info(f"阶段结束: {result.phase_name}, 状态: {result.status.value}")
        
        # 发送飞书通知
        status_emoji = {
            PhaseResultStatus.SUCCESS: "✅",
            PhaseResultStatus.CONSENSUS_REACHED: "✅",
            PhaseResultStatus.TIMEOUT: "⏰",
            PhaseResultStatus.BOSS_INTERVENTION: "👔",
            PhaseResultStatus.FAILED: "❌"
        }.get(result.status, "📋")
        
        await self._send_feishu_notification(
            f"{status_emoji} 阶段完成: {result.phase_name}\n"
            f"状态: {result.status.value}\n"
            f"轮次: {result.rounds}\n"
            f"耗时: {result.duration_seconds:.1f}秒"
        )
    
    async def _on_discussion_message(self, message: DiscussionMessage):
        """讨论消息回调"""
        # 发送到飞书
        if self.feishu_bot:
            try:
                role = self.role_map.get(message.sender)
                role_name = role.name if role else message.sender
                
                # 这里可以发送到特定群聊
                # await self.feishu_bot.send_text_message(chat_id, f"[{role_name}]: {message.content}")
                pass
            except Exception as e:
                logger.error(f"发送消息到飞书失败: {e}")
    
    # ============ 飞书集成 ============
    
    async def _send_feishu_notification(self, message: str):
        """发送飞书通知"""
        if not self.feishu_bot:
            return
        
        try:
            # 这里可以实现发送到指定用户或群聊
            logger.info(f"飞书通知: {message[:100]}...")
        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")
    
    # ============ 数据持久化 ============
    
    def _save_project_results(self):
        """保存项目结果"""
        if not self.current_project:
            return
        
        filepath = os.path.join(
            self.config.output_dir,
            f"{self.current_project}_results.json"
        )
        
        data = {
            "project": self.current_project,
            "idea": self.current_idea,
            "created_at": datetime.now().isoformat(),
            "phases": {k: v.to_dict() for k, v in self.phase_results.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"项目结果已保存: {filepath}")
    
    def save_state(self, filepath: Optional[str] = None):
        """保存状态"""
        if filepath is None:
            filepath = os.path.join(self.config.data_dir, "state.json")
        
        state = {
            "status": self.status.value,
            "current_project": self.current_project,
            "current_idea": self.current_idea,
            "phase_results": {k: v.to_dict() for k, v in self.phase_results.items()},
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"状态已保存: {filepath}")
    
    def load_state(self, filepath: Optional[str] = None):
        """加载状态"""
        if filepath is None:
            filepath = os.path.join(self.config.data_dir, "state.json")
        
        if not os.path.exists(filepath):
            logger.warning(f"状态文件不存在: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.status = ProjectStatus(state.get("status", "idle"))
            self.current_project = state.get("current_project")
            self.current_idea = state.get("current_idea")
            
            logger.info(f"状态已加载: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return False
    
    # ============ 查询接口 ============
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "status": self.status.value,
            "project": self.current_project,
            "progress": self.workflow_manager.get_progress() if hasattr(self, 'workflow_manager') else None
        }
    
    def get_phase_results(self) -> Dict[str, PhaseResult]:
        """获取阶段结果"""
        return self.phase_results
    
    def get_roles(self) -> List[Dict[str, Any]]:
        """获取角色列表"""
        return [
            {
                "id": r.role_id,
                "name": r.name,
                "profile": r.profile.profile,
                "goal": r.profile.goal
            }
            for r in self.roles
        ]
    
    def get_phases(self) -> List[Dict[str, Any]]:
        """获取阶段列表"""
        return [
            {
                "id": p.phase_id,
                "name": p.name,
                "description": p.config.description,
                "status": p.status.value,
                "deliverable_type": p.config.deliverable_type
            }
            for p in self.phase_manager.get_all_phases()
        ]
    
    # ============ Web服务器 ============
    
    def create_web_app(self):
        """创建Web应用（FastAPI）"""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            
            app = FastAPI(title="Agent Company API")
            
            @app.get("/")
            async def root():
                return {
                    "name": "Agent Company",
                    "version": "1.0.0",
                    "status": self.status.value
                }
            
            @app.get("/status")
            async def get_status():
                return self.get_status()
            
            @app.get("/roles")
            async def get_roles():
                return {"roles": self.get_roles()}
            
            @app.get("/phases")
            async def get_phases():
                return {"phases": self.get_phases()}
            
            @app.post("/projects")
            async def create_project(request: dict):
                idea = request.get("idea")
                if not idea:
                    raise HTTPException(status_code=400, detail="缺少idea参数")
                
                project_name = request.get("name")
                result = await self.start_project(idea, project_name)
                return result
            
            @app.get("/projects/current")
            async def get_current_project():
                return {
                    "project": self.current_project,
                    "idea": self.current_idea,
                    "results": {k: v.to_dict() for k, v in self.phase_results.items()}
                }
            
            @app.post("/projects/stop")
            async def stop_project():
                self.stop_project()
                return {"success": True}
            
            # 飞书Webhook
            if self.feishu_bot:
                feishu_app = self.feishu_bot.create_app()
                app.mount("/webhook", feishu_app)
            
            return app
            
        except ImportError:
            logger.error("FastAPI未安装，无法创建Web应用")
            return None


# ============ 工厂函数 ============

def create_company(config_path: str = "/mnt/okcomputer/output/config.yaml") -> AgentCompany:
    """
    创建Agent Company实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        AgentCompany实例
    """
    config = CompanyConfig.from_yaml(config_path)
    return AgentCompany(config)


async def main():
    """主函数（测试用）"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建公司
    company = create_company()
    
    # 启动测试项目
    idea = "开发一个简单的待办事项管理应用，支持添加、删除、标记完成任务"
    result = await company.start_project(idea, "TodoApp")
    
    print(f"项目结果: {json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
