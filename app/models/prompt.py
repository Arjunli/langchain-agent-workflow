"""Prompt 模型"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class PromptType(str, Enum):
    """Prompt 类型"""
    SYSTEM = "system"  # 系统提示词
    USER = "user"  # 用户提示词
    ASSISTANT = "assistant"  # 助手提示词
    TEMPLATE = "template"  # 模板提示词（包含变量）


class PromptTemplate(BaseModel):
    """Prompt 模板模型"""
    id: str = Field(..., description="Prompt ID")
    name: str = Field(..., description="Prompt 名称")
    description: Optional[str] = Field(None, description="Prompt 描述")
    
    # Prompt 内容
    content: str = Field(..., description="Prompt 内容（支持变量替换，如 {variable_name}）")
    prompt_type: PromptType = Field(default=PromptType.TEMPLATE, description="Prompt 类型")
    
    # 变量定义
    variables: List[str] = Field(default_factory=list, description="可用变量列表（如 ['workflow_list', 'user_input']）")
    
    # 使用场景
    category: Optional[str] = Field(None, description="分类（如 'workflow', 'chat', 'analysis'）")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")
    is_default: bool = Field(default=False, description="是否为默认 Prompt")
    is_active: bool = Field(default=True, description="是否启用")
    
    def render(self, **kwargs) -> str:
        """渲染 Prompt（替换变量）"""
        try:
            return self.content.format(**kwargs)
        except KeyError as e:
            # 如果缺少变量，返回原内容并记录警告
            import logging
            logging.warning(f"Prompt 渲染缺少变量: {e}")
            return self.content


class PromptUsage(BaseModel):
    """Prompt 使用记录"""
    id: str = Field(..., description="使用记录ID")
    prompt_id: str = Field(..., description="Prompt ID")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    variables_used: Dict[str, Any] = Field(default_factory=dict, description="使用的变量")
    created_at: datetime = Field(default_factory=datetime.now, description="使用时间")

