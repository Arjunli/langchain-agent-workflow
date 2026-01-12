"""消息模型"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID（可选）")
    workflow_id: Optional[str] = Field(None, description="指定工作流ID（可选）")
    prompt_id: Optional[str] = Field(None, description="指定 Prompt ID（可选，使用自定义 Prompt）")
    stream: bool = Field(default=False, description="是否流式响应")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str = Field(..., description="Agent 响应")
    conversation_id: str = Field(..., description="对话ID")
    workflow_id: Optional[str] = Field(None, description="执行的工作流ID")
    workflow_status: Optional[str] = Field(None, description="工作流状态")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用记录")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class Conversation(BaseModel):
    """对话模型"""
    id: str = Field(..., description="对话ID")
    messages: List[Message] = Field(default_factory=list, description="消息列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

