"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import api_router
from app.tools import tool_registry
from app.tools.api_tool import APICallTool
from app.tools.file_tool import FileOperationTool
from app.tools.data_tool import DataProcessingTool
from app.tools.code_tool import CodeExecutionTool
from app.storage.knowledge_store import KnowledgeStore
from app.utils.logger import setup_logging, get_logger
from app.middleware.logging import LoggingMiddleware
from app.middleware.exception import (
    exception_handler,
    http_exception_handler,
    validation_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 设置日志系统
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    enable_file_logging=settings.enable_file_logging,
    enable_console_logging=settings.enable_console_logging,
    json_format=settings.log_json_format,
)

logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志中间件（必须在CORS之后，路由之前）
app.add_middleware(LoggingMiddleware)

# 注册异常处理器
app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 注册 API 路由
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用启动中...")
    
    # 注册默认工具
    tool_registry.register(APICallTool())
    tool_registry.register(FileOperationTool())
    tool_registry.register(DataProcessingTool())
    # 注意：代码执行工具在生产环境需要沙箱，这里仅作为示例
    # tool_registry.register(CodeExecutionTool())
    
    # 初始化知识库存储
    try:
        knowledge_store = KnowledgeStore()
        logger.info("知识库存储已初始化")
    except Exception as e:
        logger.warning(f"知识库存储初始化失败: {e}")
    
    # 初始化消息队列（如果启用）
    # 注意：队列管理器连接会在首次使用时延迟初始化
    if settings.queue_enabled:
        logger.info("消息队列已启用（延迟连接）")
    
    logger.info(f"已注册 {len(tool_registry.list_tools())} 个工具")
    logger.info("应用启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用关闭中...")
    
    # 关闭消息队列连接
    if settings.queue_enabled:
        try:
            from app.api.workflow import queue_manager
            await queue_manager.disconnect()
            logger.info("消息队列连接已关闭")
        except Exception as e:
            logger.warning(f"关闭消息队列连接失败: {e}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "LangChain Agent 工作流系统",
        "version": settings.api_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

