"""Agent 状态模型"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentState(BaseModel):
    """Agent 状态"""
    conversation_id: str = Field(..., description="对话ID")
    current_workflow_id: Optional[str] = Field(None, description="当前工作流ID")
    workflow_history: List[str] = Field(default_factory=list, description="工作流执行历史")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用历史")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class AgentResponse(BaseModel):
    """Agent 响应"""
    message: str = Field(..., description="响应消息")
    workflow_triggered: bool = Field(default=False, description="是否触发了工作流")
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用")
    reasoning: Optional[str] = Field(None, description="推理过程")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

