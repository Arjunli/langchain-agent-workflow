"""RPA 处理工具"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from app.tools.registry import BaseTool
import logging
import asyncio

logger = logging.getLogger(__name__)

# 添加 RPA 模块路径到 sys.path
# 假设项目结构是: langchain/agent/ 和 langchain/rpa/
_current_dir = Path(__file__).parent  # agent/app/tools/
_project_root = _current_dir.parent.parent.parent  # langchain/
_rpa_path = _project_root / "rpa"
if _rpa_path.exists() and str(_rpa_path) not in sys.path:
    sys.path.insert(0, str(_rpa_path))
    logger.info(f"已添加 RPA 模块路径: {_rpa_path}")
elif not _rpa_path.exists():
    logger.warning(f"RPA 模块路径不存在: {_rpa_path}，RPA 功能可能不可用")


class RPATool(BaseTool):
    """RPA 处理工具，用于处理 Excel、PDF、Web 等文件"""
    
    def __init__(self):
        super().__init__(
            name="rpa_process",
            description="RPA 文件处理工具，支持处理 Excel、PDF、Web 等文件类型。可以自动识别文件类型并使用相应的插件进行处理。"
        )
        self._rpa_initialized = False
    
    def _initialize_rpa(self):
        """初始化 RPA 模块"""
        if self._rpa_initialized:
            return
        
        try:
            # 导入 RPA 模块
            from main import initialize_app
            initialize_app()
            self._rpa_initialized = True
            logger.info("RPA 模块初始化成功")
        except Exception as e:
            logger.error(f"RPA 模块初始化失败: {e}")
            raise
    
    def run(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行 RPA 文件处理（同步）
        
        参数:
            file_path: 要处理的文件路径
            options: 可选的处理选项（字典格式）
        
        返回:
            处理结果字典，包含：
            - status: 处理状态（success/error）
            - result: 处理结果详情
            - trace_id: 追踪ID
            - request_id: 请求ID
        """
        try:
            # 初始化 RPA 模块
            self._initialize_rpa()
            
            # 验证文件路径
            path = Path(file_path)
            if not path.exists():
                return {
                    "error": f"文件不存在: {file_path}",
                    "status": "error"
                }
            
            # 转换为绝对路径
            file_path = str(path.absolute())
            
            logger.info(f"开始处理文件: {file_path}")
            
            # 导入并调用 RPA 处理函数
            from main import process_file
            
            # 调用 RPA 处理
            result = process_file(file_path, options)
            
            logger.info(f"文件处理完成: {file_path}, 状态: {result.get('status', 'unknown')}")
            
            return {
                "success": result.get("status") != "error",
                "status": result.get("status", "unknown"),
                "result": result,
                "trace_id": result.get("trace_id"),
                "request_id": result.get("request_id"),
                "file_path": file_path
            }
        
        except ImportError as e:
            error_msg = f"无法导入 RPA 模块: {e}。请确保 RPA 模块路径正确。"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "error"
            }
        except Exception as e:
            error_msg = f"RPA 处理失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "error",
                "file_path": file_path
            }
    
    async def run_async(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        异步执行 RPA 文件处理
        
        参数:
            file_path: 要处理的文件路径
            options: 可选的处理选项（字典格式）
        
        返回:
            处理结果字典
        """
        try:
            # 初始化 RPA 模块
            self._initialize_rpa()
            
            # 验证文件路径
            path = Path(file_path)
            if not path.exists():
                return {
                    "error": f"文件不存在: {file_path}",
                    "status": "error"
                }
            
            # 转换为绝对路径
            file_path = str(path.absolute())
            
            logger.info(f"开始异步处理文件: {file_path}")
            
            # 导入 RPA 异步处理函数
            from core.rpa_processor import async_process_file
            from utils.context import (
                generate_trace_id, generate_request_id,
                set_trace_id, set_request_id
            )
            
            # 生成上下文
            trace_id = generate_trace_id()
            request_id = generate_request_id()
            set_trace_id(trace_id)
            set_request_id(request_id)
            
            # 调用异步处理
            result = await async_process_file(file_path, options)
            
            # 添加追踪信息
            result["trace_id"] = trace_id
            result["request_id"] = request_id
            
            logger.info(f"文件异步处理完成: {file_path}, 状态: {result.get('status', 'unknown')}")
            
            return {
                "success": result.get("status") != "error",
                "status": result.get("status", "unknown"),
                "result": result,
                "trace_id": trace_id,
                "request_id": request_id,
                "file_path": file_path
            }
        
        except ImportError as e:
            error_msg = f"无法导入 RPA 模块: {e}。请确保 RPA 模块路径正确。"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "status": "error"
            }
        except Exception as e:
            error_msg = f"RPA 异步处理失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "error",
                "file_path": file_path
            }
