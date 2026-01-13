"""统一异常处理中间件"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.response import error_response, ResponseCode
from app.utils.logger import get_logger
import traceback

logger = get_logger(__name__)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: 异常对象
    
    Returns:
        JSONResponse错误响应
    """
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={"path": request.url.path, "method": request.method},
        exc_info=True
    )
    
    error_resp = error_response(
        message="Internal server error",
        code=ResponseCode.INTERNAL_ERROR,
        request=request,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_resp.model_dump()
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: HTTPException对象
    
    Returns:
        JSONResponse错误响应
    """
    # 映射HTTP状态码到ResponseCode
    code_mapping = {
        400: ResponseCode.BAD_REQUEST,
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        409: ResponseCode.CONFLICT,
        422: ResponseCode.VALIDATION_ERROR,
        500: ResponseCode.INTERNAL_ERROR,
        503: ResponseCode.SERVICE_UNAVAILABLE,
        504: ResponseCode.TIMEOUT,
    }
    
    code = code_mapping.get(exc.status_code, ResponseCode.INTERNAL_ERROR)
    
    error_resp = error_response(
        message=str(exc.detail) if exc.detail else "HTTP error",
        code=code,
        request=request,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_resp.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: RequestValidationError对象
    
    Returns:
        JSONResponse错误响应
    """
    from app.models.response import ErrorDetail
    
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            field=".".join(str(loc) for loc in error.get("loc", [])),
            message=error.get("msg", "validation error"),
            code=error.get("type")
        ))
    
    error_resp = error_response(
        message="Request validation failed",
        code=ResponseCode.VALIDATION_ERROR,
        errors=errors,
        request=request,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_resp.model_dump()
    )
