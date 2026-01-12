"""任务模型"""
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TaskType(str, Enum):
    """任务类型"""
    WORKFLOW_EXECUTE = "workflow_execute"  # 工作流执行
    CHAT_PROCESS = "chat_process"  # 聊天处理
    KNOWLEDGE_SEARCH = "knowledge_search"  # 知识库搜索


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"  # 等待处理
    QUEUED = "queued"  # 已入队
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


class Task(BaseModel):
    """任务模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    
    # 任务参数
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    
    # 任务结果
    result: Optional[Any] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    # 重试相关
    retry_count: int = Field(default=0, description="重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }



