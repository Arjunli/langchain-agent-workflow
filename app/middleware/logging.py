"""日志中间件"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.utils.logger import (
    get_logger,
    set_trace_id,
    set_request_id,
    clear_context,
    get_trace_id
)

logger = get_logger(__name__)
access_logger = get_logger("access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件：自动注入trace_id和request_id"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成追踪ID和请求ID
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        # 设置上下文
        set_trace_id(trace_id)
        set_request_id(request_id)
        
        # 记录请求开始
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        access_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
            }
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            access_logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "client_ip": client_ip,
                }
            )
            
            # 添加追踪ID到响应头
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Request-Id"] = request_id
            
            return response
        
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求错误
            access_logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": process_time,
                    "client_ip": client_ip,
                },
                exc_info=True
            )
            
            raise
        
        finally:
            # 清除上下文（可选，因为contextvars会自动处理）
            # clear_context()
            pass


class TraceContextMiddleware(BaseHTTPMiddleware):
    """追踪上下文中间件：确保trace_id在异步调用中传递"""
    
    async def dispatch(self, request: Request, call_next):
        # 从请求头获取或生成trace_id
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        set_trace_id(trace_id)
        
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        
        return response



