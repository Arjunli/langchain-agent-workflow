"""统一响应工具函数"""
from typing import Optional, Any, TypeVar
from fastapi import Request
from fastapi.responses import JSONResponse
from app.models.response import (
    BaseResponse, 
    ErrorResponse, 
    ResponseCode,
    PaginatedResponse,
    PaginationMeta,
    ErrorDetail
)
from app.utils.logger import get_trace_id, get_request_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = ResponseCode.SUCCESS,
    request: Optional[Request] = None
) -> BaseResponse:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        request: FastAPI请求对象（可选，用于获取trace_id等）
    
    Returns:
        BaseResponse对象
    """
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        request: FastAPI请求对象（用于获取trace_id等）
    
    Returns:
        BaseResponse对象
    """
    trace_id = get_trace_id()
    request_id = get_request_id()
    
    return BaseResponse(
        code=code,
        message=message,
        data=data,
        trace_id=trace_id,
        request_id=request_id
    )


def error_response(
    message: str,
    code: int = ResponseCode.INTERNAL_ERROR,
    errors: Optional[list[ErrorDetail]] = None,
    request: Optional[Request] = None,
    path: Optional[str] = None
) -> ErrorResponse:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        code: 状态码
        errors: 详细错误列表
        request: FastAPI请求对象
        path: 请求路径
    
    Returns:
        ErrorResponse对象
    """
    trace_id = get_trace_id()
    request_id = get_request_id()
    
    if request and not path:
        path = request.url.path
    
    return ErrorResponse(
        code=code,
        message=message,
        errors=errors,
        trace_id=trace_id,
        request_id=request_id,
        path=path
    )


def paginated_response(
    data: list[Any],
    page: int,
    page_size: int,
    total: int,
    message: str = "success",
    code: int = ResponseCode.SUCCESS,
    request: Optional[Request] = None
) -> PaginatedResponse:
    """
    创建分页响应
    
    Args:
        data: 数据列表
        page: 当前页码
        page_size: 每页数量
        total: 总数量
        message: 响应消息
        code: 状态码
        request: FastAPI请求对象
    
    Returns:
        PaginatedResponse对象
    """
    trace_id = get_trace_id()
    request_id = get_request_id()
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return PaginatedResponse(
        code=code,
        message=message,
        data=data,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        ),
        trace_id=trace_id,
        request_id=request_id
    )


def created_response(
    data: Any = None,
    message: str = "created",
    request: Optional[Request] = None
) -> BaseResponse:
    """创建资源成功响应"""
    return success_response(
        data=data,
        message=message,
        code=ResponseCode.CREATED,
        request=request
    )


def not_found_response(
    resource: str = "resource",
    request: Optional[Request] = None
) -> ErrorResponse:
    """资源不存在响应"""
    return error_response(
        message=f"{resource} not found",
        code=ResponseCode.NOT_FOUND,
        request=request
    )


def validation_error_response(
    errors: list[ErrorDetail],
    message: str = "validation error",
    request: Optional[Request] = None
) -> ErrorResponse:
    """验证错误响应"""
    return error_response(
        message=message,
        code=ResponseCode.VALIDATION_ERROR,
        errors=errors,
        request=request
    )


def bad_request_response(
    message: str = "bad request",
    errors: Optional[list[ErrorDetail]] = None,
    request: Optional[Request] = None
) -> ErrorResponse:
    """请求错误响应"""
    return error_response(
        message=message,
        code=ResponseCode.BAD_REQUEST,
        errors=errors,
        request=request
    )


def internal_error_response(
    message: str = "internal server error",
    request: Optional[Request] = None
) -> ErrorResponse:
    """服务器内部错误响应"""
    return error_response(
        message=message,
        code=ResponseCode.INTERNAL_ERROR,
        request=request
    )
