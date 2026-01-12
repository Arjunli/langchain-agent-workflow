"""结构化日志系统"""
import logging
import json
import sys
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback

# 上下文变量：存储请求追踪信息
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
coroutine_id_var: ContextVar[Optional[str]] = ContextVar('coroutine_id', default=None)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器（JSON格式）"""
    
    def __init__(self, include_thread_info: bool = True, include_coroutine_info: bool = True):
        super().__init__()
        self.include_thread_info = include_thread_info
        self.include_coroutine_info = include_coroutine_info
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 线程信息
        if self.include_thread_info:
            log_data["thread"] = {
                "id": record.thread,
                "name": threading.current_thread().name,
            }
        
        # 协程信息
        if self.include_coroutine_info:
            try:
                loop = asyncio.get_running_loop()
                if loop:
                    coroutine_id = id(asyncio.current_task(loop)) if asyncio.current_task(loop) else None
                    log_data["coroutine"] = {
                        "id": str(coroutine_id) if coroutine_id else None,
                        "loop_id": id(loop),
                    }
            except RuntimeError:
                # 不在事件循环中
                log_data["coroutine"] = None
        
        # 上下文信息（trace_id, request_id等）
        trace_id = trace_id_var.get()
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        coroutine_id = coroutine_id_var.get()
        
        if trace_id or request_id or user_id or coroutine_id:
            log_data["context"] = {}
            if trace_id:
                log_data["context"]["trace_id"] = trace_id
            if request_id:
                log_data["context"]["request_id"] = request_id
            if user_id:
                log_data["context"]["user_id"] = user_id
            if coroutine_id:
                log_data["context"]["coroutine_id"] = coroutine_id
        
        # 异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None,
            }
        
        # 额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class SimpleFormatter(logging.Formatter):
    """简单格式化器（用于控制台输出）"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取上下文信息
        trace_id = trace_id_var.get()
        request_id = request_id_var.get()
        thread_name = threading.current_thread().name
        
        # 构建前缀
        prefix_parts = []
        if trace_id:
            prefix_parts.append(f"[trace:{trace_id[:8]}]")
        if request_id:
            prefix_parts.append(f"[req:{request_id[:8]}]")
        prefix_parts.append(f"[{thread_name}]")
        
        # 协程信息
        try:
            loop = asyncio.get_running_loop()
            if loop:
                task = asyncio.current_task(loop)
                if task:
                    prefix_parts.append(f"[coro:{id(task)}]")
        except RuntimeError:
            pass
        
        prefix = " ".join(prefix_parts) if prefix_parts else ""
        
        # 格式化消息
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        logger_name = record.name
        message = record.getMessage()
        
        log_line = f"{timestamp} {level} {prefix} {logger_name} - {message}"
        
        # 添加异常信息
        if record.exc_info:
            log_line += f"\n{traceback.format_exception(*record.exc_info)}"
        
        return log_line


class ContextualLogger:
    """上下文感知的Logger包装器"""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加上下文信息到extra"""
        if extra is None:
            extra = {}
        
        # 添加上下文变量
        trace_id = trace_id_var.get()
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        coroutine_id = coroutine_id_var.get()
        
        if trace_id:
            extra["trace_id"] = trace_id
        if request_id:
            extra["request_id"] = request_id
        if user_id:
            extra["user_id"] = user_id
        if coroutine_id:
            extra["coroutine_id"] = coroutine_id
        
        return extra
    
    def debug(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.debug(msg, *args, extra=self._add_context(extra), **kwargs)
    
    def info(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.info(msg, *args, extra=self._add_context(extra), **kwargs)
    
    def warning(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.warning(msg, *args, extra=self._add_context(extra), **kwargs)
    
    def error(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.error(msg, *args, extra=self._add_context(extra), **kwargs)
    
    def critical(self, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.critical(msg, *args, extra=self._add_context(extra), **kwargs)
    
    def exception(self, msg: str, *args, exc_info=True, extra: Optional[Dict[str, Any]] = None, **kwargs):
        self._logger.error(msg, *args, exc_info=exc_info, extra=self._add_context(extra), **kwargs)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
        enable_file_logging: 是否启用文件日志
        enable_console_logging: 是否启用控制台日志
        json_format: 是否使用JSON格式（文件日志）
        max_bytes: 日志文件最大大小
        backup_count: 备份文件数量
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的handlers
    root_logger.handlers.clear()
    
    # 控制台handler
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = SimpleFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 文件handlers
    if enable_file_logging:
        # 所有日志（JSON格式）
        all_log_file = log_path / "app.log"
        all_handler = TimedRotatingFileHandler(
            str(all_log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8"
        )
        all_handler.setLevel(getattr(logging, log_level.upper()))
        all_formatter = StructuredFormatter() if json_format else SimpleFormatter()
        all_handler.setFormatter(all_formatter)
        root_logger.addHandler(all_handler)
        
        # 错误日志（单独文件）
        error_log_file = log_path / "error.log"
        error_handler = TimedRotatingFileHandler(
            str(error_log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count * 2,  # 错误日志保留更久
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = StructuredFormatter() if json_format else SimpleFormatter()
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # 访问日志（API请求）
        access_log_file = log_path / "access.log"
        access_handler = TimedRotatingFileHandler(
            str(access_log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8"
        )
        access_handler.setLevel(logging.INFO)
        access_formatter = StructuredFormatter() if json_format else SimpleFormatter()
        access_handler.setFormatter(access_formatter)
        # 创建专门的访问日志logger
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
        
        # Worker日志（任务处理）
        worker_log_file = log_path / "worker.log"
        worker_handler = TimedRotatingFileHandler(
            str(worker_log_file),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8"
        )
        worker_handler.setLevel(logging.INFO)
        worker_formatter = StructuredFormatter() if json_format else SimpleFormatter()
        worker_handler.setFormatter(worker_formatter)
        # 创建专门的worker日志logger
        worker_logger = logging.getLogger("worker")
        worker_logger.addHandler(worker_handler)
        worker_logger.setLevel(logging.INFO)
        worker_logger.propagate = False


def get_logger(name: str) -> ContextualLogger:
    """
    获取logger实例
    
    Args:
        name: logger名称（通常是__name__）
    
    Returns:
        ContextualLogger实例
    """
    logger = logging.getLogger(name)
    return ContextualLogger(logger)


def set_trace_id(trace_id: str):
    """设置追踪ID"""
    trace_id_var.set(trace_id)


def set_request_id(request_id: str):
    """设置请求ID"""
    request_id_var.set(request_id)


def set_user_id(user_id: str):
    """设置用户ID"""
    user_id_var.set(user_id)


def set_coroutine_id(coroutine_id: str):
    """设置协程ID"""
    coroutine_id_var.set(coroutine_id)


def get_trace_id() -> Optional[str]:
    """获取追踪ID"""
    return trace_id_var.get()


def get_request_id() -> Optional[str]:
    """获取请求ID"""
    return request_id_var.get()


def clear_context():
    """清除上下文"""
    trace_id_var.set(None)
    request_id_var.set(None)
    user_id_var.set(None)
    coroutine_id_var.set(None)



