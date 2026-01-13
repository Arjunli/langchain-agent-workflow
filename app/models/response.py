"""统一API响应模型"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from enum import IntEnum

T = TypeVar('T')


class ResponseCode(IntEnum):
    """响应状态码"""
    SUCCESS = 200  # 成功
    CREATED = 201  # 创建成功
    ACCEPTED = 202  # 已接受
    NO_CONTENT = 204  # 无内容
    
    # 客户端错误 4xx
    BAD_REQUEST = 400  # 请求错误
    UNAUTHORIZED = 401  # 未授权
    FORBIDDEN = 403  # 禁止访问
    NOT_FOUND = 404  # 资源不存在
    CONFLICT = 409  # 冲突
    VALIDATION_ERROR = 422  # 验证错误
    
    # 服务器错误 5xx
    INTERNAL_ERROR = 500  # 服务器内部错误
    SERVICE_UNAVAILABLE = 503  # 服务不可用
    TIMEOUT = 504  # 超时


class BaseResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    trace_id: Optional[str] = Field(None, description="追踪ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="错误消息")
    errors: Optional[list[ErrorDetail]] = Field(None, description="详细错误列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    trace_id: Optional[str] = Field(None, description="追踪ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    path: Optional[str] = Field(None, description="请求路径")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total: int = Field(..., description="总数量")
    total_pages: int = Field(..., description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = Field(default=ResponseCode.SUCCESS, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: list[T] = Field(default_factory=list, description="数据列表")
    meta: PaginationMeta = Field(..., description="分页元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    trace_id: Optional[str] = Field(None, description="追踪ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
