"""
富文本卡片模块
提供交互式卡片消息的构建功能
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CardTemplate(Enum):
    """卡片模板类型"""
    DEFAULT = "default"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CUSTOM = "custom"


@dataclass
class CardColor:
    """卡片颜色配置"""
    blue: str = "blue"
    wathet: str = "wathet"
    turquoise: str = "turquoise"
    green: str = "green"
    yellow: str = "yellow"
    orange: str = "orange"
    red: str = "red"
    carmine: str = "carmine"
    violet: str = "violet"
    purple: str = "purple"
    indigo: str = "indigo"
    grey: str = "grey"


class CardBuilder:
    """卡片构建器"""
    
    # 模板颜色映射
    TEMPLATE_COLORS = {
        CardTemplate.INFO: "blue",
        CardTemplate.SUCCESS: "green",
        CardTemplate.WARNING: "orange",
        CardTemplate.ERROR: "red",
        CardTemplate.DEFAULT: "grey",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.elements: List[Dict[str, Any]] = []
        self.header: Optional[Dict[str, Any]] = None
        self.config_settings: Dict[str, Any] = {
            "wide_screen_mode": True
        }
    
    def set_header(
        self, 
        title: str, 
        subtitle: Optional[str] = None,
        template: CardTemplate = CardTemplate.DEFAULT,
        custom_color: Optional[str] = None
    ) -> "CardBuilder":
        """
        设置卡片头部
        
        Args:
            title: 标题
            subtitle: 副标题
            template: 模板类型
            custom_color: 自定义颜色
        """
        self.header = {
            "title": {
                "tag": "plain_text",
                "content": title
            }
        }
        
        if subtitle:
            self.header["subtitle"] = {
                "tag": "plain_text",
                "content": subtitle
            }
        
        # 设置模板颜色
        color = custom_color or self.TEMPLATE_COLORS.get(template, "grey")
        self.header["template"] = color
        
        return self
    
    def add_markdown(self, content: str) -> "CardBuilder":
        """添加Markdown内容"""
        self.elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
        return self
    
    def add_plain_text(self, content: str) -> "CardBuilder":
        """添加纯文本内容"""
        self.elements.append({
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": content
            }
        })
        return self
    
    def add_column_set(
        self, 
        columns: List[Dict[str, Any]], 
        flex_mode: str = "none",
        background_style: str = "default"
    ) -> "CardBuilder":
        """
        添加多列布局
        
        Args:
            columns: 列配置列表
            flex_mode: 弹性模式 (none, stretch, flow)
            background_style: 背景样式
        """
        self.elements.append({
            "tag": "column_set",
            "flex_mode": flex_mode,
            "background_style": background_style,
            "columns": columns
        })
        return self
    
    def add_column(
        self, 
        elements: List[Dict[str, Any]], 
        width: str = "auto",
        weight: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建列配置
        
        Args:
            elements: 列内元素
            width: 宽度 (auto, weighted)
            weight: 权重
        """
        column = {
            "tag": "column",
            "width": width,
            "elements": elements
        }
        if weight is not None:
            column["weight"] = weight
        return column
    
    def add_image(
        self, 
        image_key: str, 
        alt: str = "",
        preview: bool = True,
        mode: str = "fit_horizontal"
    ) -> "CardBuilder":
        """
        添加图片
        
        Args:
            image_key: 图片key
            alt: 替代文本
            preview: 是否可预览
            mode: 显示模式
        """
        self.elements.append({
            "tag": "img",
            "img_key": image_key,
            "alt": {
                "tag": "plain_text",
                "content": alt
            },
            "preview": preview,
            "mode": mode
        })
        return self
    
    def add_divider(self) -> "CardBuilder":
        """添加分割线"""
        self.elements.append({"tag": "hr"})
        return self
    
    def add_note(self, content: str) -> "CardBuilder":
        """添加备注"""
        self.elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": content
                }
            ]
        })
        return self
    
    def add_actions(
        self, 
        actions: List[Dict[str, Any]], 
        layout: str = "default"
    ) -> "CardBuilder":
        """
        添加操作按钮
        
        Args:
            actions: 按钮配置列表
            layout: 布局 (default, bisected, trisection, flow)
        """
        self.elements.append({
            "tag": "action",
            "actions": actions,
            "layout": layout
        })
        return self
    
    def create_button(
        self,
        text: str,
        action_type: str = "default",
        value: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
        multi_url: Optional[Dict[str, str]] = None,
        confirm: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        创建按钮
        
        Args:
            text: 按钮文本
            action_type: 按钮类型 (default, primary, danger)
            value: 回调值
            url: 跳转链接
            multi_url: 多平台链接
            confirm: 确认对话框配置
        """
        button = {
            "tag": "button",
            "text": {
                "tag": "plain_text",
                "content": text
            },
            "type": action_type
        }
        
        if value:
            button["value"] = value
        if url:
            button["url"] = url
        if multi_url:
            button["multi_url"] = multi_url
        if confirm:
            button["confirm"] = confirm
        
        return button
    
    def create_select_static(
        self,
        placeholder: str,
        options: List[Dict[str, str]],
        value: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建静态选择器
        
        Args:
            placeholder: 占位符
            options: 选项列表 [{"text": "显示文本", "value": "值"}]
            value: 默认值
        """
        select = {
            "tag": "select_static",
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder
            },
            "options": [
                {
                    "text": {
                        "tag": "plain_text",
                        "content": opt["text"]
                    },
                    "value": opt["value"]
                }
                for opt in options
            ]
        }
        if value:
            select["value"] = value
        return select
    
    def create_input(
        self,
        placeholder: str,
        name: str,
        default_value: str = "",
        max_length: int = 100
    ) -> Dict[str, Any]:
        """
        创建输入框
        
        Args:
            placeholder: 占位符
            name: 字段名
            default_value: 默认值
            max_length: 最大长度
        """
        return {
            "tag": "input",
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder
            },
            "name": name,
            "default_value": default_value,
            "max_length": max_length
        }
    
    def add_user_info(
        self,
        avatar: str,
        name: str,
        subtitle: Optional[str] = None,
        extra: Optional[str] = None
    ) -> "CardBuilder":
        """
        添加用户信息展示
        
        Args:
            avatar: 头像URL或image_key
            name: 用户名
            subtitle: 副标题
            extra: 额外信息
        """
        elements = [
            {
                "tag": "img",
                "img_key": avatar,
                "circle": True,
                "preview": False,
                "width": "40px",
                "height": "40px"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": name
                }
            }
        ]
        
        if subtitle:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": subtitle
                }
            })
        
        if extra:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": extra
                }
            })
        
        column = self.add_column(elements, width="weighted", weight=1)
        self.add_column_set([column])
        
        return self
    
    def add_speaker_card(
        self,
        avatar: str,
        name: str,
        content: str,
        round_num: int,
        timestamp: Optional[str] = None
    ) -> "CardBuilder":
        """
        添加发言者卡片（用于会议/讨论场景）
        
        Args:
            avatar: 头像
            name: 发言者名称
            content: 发言内容
            round_num: 当前轮数
            timestamp: 时间戳
        """
        # 头部：头像和名称
        header_elements = [
            {
                "tag": "img",
                "img_key": avatar,
                "circle": True,
                "preview": False,
                "width": "36px",
                "height": "36px"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{name}**"
                }
            }
        ]
        
        if timestamp:
            header_elements.append({
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": timestamp
                }
            })
        
        header_column = self.add_column(header_elements, width="weighted", weight=1)
        
        # 轮数标签
        round_column = self.add_column([
            {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": f"第{round_num}轮"
                }
            }
        ], width="auto")
        
        self.add_column_set([header_column, round_column])
        
        # 内容区域
        self.add_markdown(content)
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建卡片"""
        card = {
            "config": self.config_settings,
            "elements": self.elements
        }
        
        if self.header:
            card["header"] = self.header
        
        return card
    
    @staticmethod
    def create_meeting_summary_card(
        title: str,
        speakers: List[Dict[str, Any]],
        current_round: int,
        total_rounds: int
    ) -> Dict[str, Any]:
        """
        创建会议摘要卡片
        
        Args:
            title: 会议标题
            speakers: 发言者列表 [{"avatar": "", "name": "", "content": ""}]
            current_round: 当前轮数
            total_rounds: 总轮数
        """
        builder = CardBuilder()
        
        # 设置头部
        builder.set_header(
            title=title,
            subtitle=f"第 {current_round}/{total_rounds} 轮讨论",
            template=CardTemplate.INFO
        )
        
        builder.add_divider()
        
        # 添加每个发言者
        for i, speaker in enumerate(speakers):
            builder.add_speaker_card(
                avatar=speaker.get("avatar", ""),
                name=speaker.get("name", "未知用户"),
                content=speaker.get("content", ""),
                round_num=current_round,
                timestamp=speaker.get("timestamp")
            )
            
            if i < len(speakers) - 1:
                builder.add_divider()
        
        # 添加进度说明
        builder.add_note(f"当前进度: {current_round}/{total_rounds} 轮")
        
        return builder.build()
    
    @staticmethod
    def create_reminder_card(
        title: str,
        message: str,
        mentioned_users: List[str],
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """
        创建提醒卡片
        
        Args:
            title: 提醒标题
            message: 提醒内容
            mentioned_users: @的用户列表
            urgency: 紧急程度 (low, normal, high, urgent)
        """
        template_map = {
            "low": CardTemplate.DEFAULT,
            "normal": CardTemplate.INFO,
            "high": CardTemplate.WARNING,
            "urgent": CardTemplate.ERROR
        }
        
        builder = CardBuilder()
        builder.set_header(
            title=f"⏰ {title}",
            template=template_map.get(urgency, CardTemplate.INFO)
        )
        
        # @提醒
        if mentioned_users:
            at_text = " ".join([f"<at user_id='{uid}'></at>" for uid in mentioned_users])
            builder.add_markdown(at_text)
        
        builder.add_markdown(message)
        
        return builder.build()
    
    @staticmethod
    def create_progress_card(
        title: str,
        progress: float,
        status_text: str,
        details: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建进度卡片
        
        Args:
            title: 标题
            progress: 进度 (0-100)
            status_text: 状态文本
            details: 详细信息列表
        """
        builder = CardBuilder()
        
        # 根据进度选择模板
        if progress >= 100:
            template = CardTemplate.SUCCESS
        elif progress >= 70:
            template = CardTemplate.INFO
        elif progress >= 40:
            template = CardTemplate.WARNING
        else:
            template = CardTemplate.DEFAULT
        
        builder.set_header(title=title, template=template)
        
        # 进度条（使用文本模拟）
        filled = int(progress / 10)
        empty = 10 - filled
        progress_bar = "█" * filled + "░" * empty
        
        builder.add_markdown(f"**进度:** {progress}%")
        builder.add_markdown(f"`{progress_bar}`")
        builder.add_plain_text(f"状态: {status_text}")
        
        if details:
            builder.add_divider()
            for detail in details:
                builder.add_plain_text(f"• {detail}")
        
        return builder.build()
