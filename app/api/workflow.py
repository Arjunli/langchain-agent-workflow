"""工作流管理 API"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from app.models.workflow import Workflow
from app.models.task import Task, TaskType, TaskStatus
from app.models.response import BaseResponse, ResponseCode
from app.utils.response import (
    success_response,
    created_response,
    not_found_response,
    internal_error_response,
    bad_request_response
)
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.tools import tool_registry
from app.queue.manager import QueueManager
from app.config import settings
from app.utils.logger import get_logger, get_trace_id
import tempfile
import os
from contextlib import contextmanager

logger = get_logger(__name__)

router = APIRouter()

# 初始化组件
workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(workflow_registry, tool_registry)
queue_manager = QueueManager()

# 确保队列管理器在启动时连接（延迟初始化）
_queue_manager_initialized = False

async def get_queue_manager() -> QueueManager:
    """获取队列管理器（延迟初始化）"""
    global _queue_manager_initialized
    if not _queue_manager_initialized:
        try:
            await queue_manager.connect()
            _queue_manager_initialized = True
        except Exception as e:
            logger.warning(f"队列管理器连接失败: {e}")
    return queue_manager


@router.post("", response_model=BaseResponse[Workflow])
async def create_workflow(workflow: Workflow, request: Request) -> BaseResponse[Workflow]:
    """创建工作流"""
    try:
        workflow_engine.register_workflow(workflow)
        return created_response(
            data=workflow,
            message="工作流创建成功",
            request=request
        )
    except Exception as e:
        logger.error(f"创建工作流失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"创建工作流失败: {str(e)}",
            request=request
        )


@router.post("/upload", response_model=BaseResponse[Workflow])
async def upload_workflow(request: Request, file: UploadFile = File(...)) -> BaseResponse[Workflow]:
    """上传工作流文件（YAML/JSON）"""
    try:
        content = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        
        # 保存临时文件（使用context manager确保清理）
        @contextmanager
        def temp_file_manager(content: bytes, suffix: str):
            """临时文件管理器，确保文件总是被清理"""
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=suffix) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                yield tmp_path
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                        logger.debug(f"临时文件已清理: {tmp_path}")
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {tmp_path}, 错误: {e}")
        
        with temp_file_manager(content, f'.{file_ext}') as tmp_path:
            if file_ext == 'yaml' or file_ext == 'yml':
                workflow = workflow_registry.load_from_yaml(tmp_path)
            elif file_ext == 'json':
                workflow = workflow_registry.load_from_json(tmp_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
            
            workflow_engine.register_workflow(workflow)
            return created_response(
                data=workflow,
                message="工作流上传成功",
                request=request
            )
    
    except Exception as e:
        logger.error(f"上传工作流失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"上传工作流失败: {str(e)}",
            request=request
        )


@router.get("", response_model=BaseResponse[List[Workflow]])
async def list_workflows(request: Request) -> BaseResponse[List[Workflow]]:
    """列出所有工作流"""
    workflows = workflow_engine.list_workflows()
    return success_response(
        data=workflows,
        message="获取工作流列表成功",
        request=request
    )


@router.get("/{workflow_id}", response_model=BaseResponse[Workflow])
async def get_workflow(workflow_id: str, request: Request) -> BaseResponse[Workflow]:
    """获取工作流"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        return not_found_response(
            resource=f"工作流 {workflow_id}",
            request=request
        )
    return success_response(
        data=workflow,
        message="获取工作流成功",
        request=request
    )


@router.post("/{workflow_id}/execute", response_model=BaseResponse[Dict[str, Any]])
async def execute_workflow(
    workflow_id: str,
    variables: Dict[str, Any] = None,
    async_execute: bool = Query(default=True, description="是否异步执行"),
    request: Request = None
) -> BaseResponse[Dict[str, Any]]:
    """
    执行工作流
    
    Args:
        workflow_id: 工作流ID
        variables: 工作流变量
        async_execute: 是否异步执行（使用消息队列）
    
    Returns:
        如果异步执行，返回任务ID和状态；否则返回工作流执行结果
    """
    try:
        # 检查工作流是否存在
        workflow = workflow_engine.get_workflow(workflow_id)
        if not workflow:
            return not_found_response(
                resource=f"工作流 {workflow_id}",
                request=request
            )
        
        # 如果启用异步执行且消息队列可用
        if async_execute and settings.queue_enabled:
            try:
                # 创建任务
                task = Task(
                    type=TaskType.WORKFLOW_EXECUTE,
                    params={
                        "workflow_id": workflow_id,
                        "variables": variables or {}
                    },
                    metadata={
                        "workflow_name": workflow.name,
                        "workflow_version": workflow.version,
                        "trace_id": get_trace_id(),  # 传递trace_id到任务
                    }
                )
                
                # 获取队列管理器并加入队列
                qm = await get_queue_manager()
                task_id = await qm.enqueue_task(task)
                
                return success_response(
                    data={
                        "task_id": task_id,
                        "status": "queued",
                        "workflow_id": workflow_id
                    },
                    message="工作流已加入执行队列",
                    request=request
                )
            except Exception as e:
                logger.warning(f"消息队列不可用，使用同步执行: {e}")
                # 降级到同步执行
                result = await workflow_engine.execute_workflow(workflow_id, variables)
                return success_response(
                    data={
                        "task_id": None,
                        "status": result.status.value,
                        "workflow": result.model_dump()
                    },
                    message="工作流已同步执行完成",
                    request=request
                )
        else:
            # 同步执行
            result = await workflow_engine.execute_workflow(workflow_id, variables)
            return success_response(
                data={
                    "task_id": None,
                    "status": result.status.value,
                    "workflow": result.model_dump()
                },
                message="工作流已同步执行完成",
                request=request
            )
    
    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"执行工作流失败: {str(e)}",
            request=request
        )


@router.get("/search/{keyword}", response_model=BaseResponse[List[Workflow]])
async def search_workflows(keyword: str, request: Request) -> BaseResponse[List[Workflow]]:
    """搜索工作流"""
    workflows = workflow_engine.search_workflows(keyword)
    return success_response(
        data=workflows,
        message=f"搜索到 {len(workflows)} 个工作流",
        request=request
    )


@router.get("/tasks/{task_id}", response_model=BaseResponse[Dict[str, Any]])
async def get_task_status(task_id: str, request: Request) -> BaseResponse[Dict[str, Any]]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态信息
    """
    try:
        qm = await get_queue_manager()
        task = await qm.get_task(task_id)
        if not task:
            return not_found_response(
                resource=f"任务 {task_id}",
                request=request
            )
        
        task_data = {
            "task_id": task.id,
            "type": task.type.value,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "metadata": task.metadata
        }
        
        return success_response(
            data=task_data,
            message="获取任务状态成功",
            request=request
        )
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"获取任务状态失败: {str(e)}",
            request=request
        )


@router.post("/tasks/{task_id}/cancel", response_model=BaseResponse[Dict[str, Any]])
async def cancel_task(task_id: str, request: Request) -> BaseResponse[Dict[str, Any]]:
    """
    取消任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        取消结果
    """
    try:
        qm = await get_queue_manager()
        success = await qm.cancel_task(task_id)
        if not success:
            return bad_request_response(
                message="任务无法取消（可能已开始执行或不存在）",
                request=request
            )
        
        return success_response(
            data={
                "task_id": task_id,
                "status": "cancelled"
            },
            message="任务已取消",
            request=request
        )
    except Exception as e:
        logger.error(f"取消任务失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"取消任务失败: {str(e)}",
            request=request
        )


@router.get("/queue/stats", response_model=BaseResponse[Dict[str, Any]])
async def get_queue_stats(request: Request) -> BaseResponse[Dict[str, Any]]:
    """
    获取队列统计信息
    
    Returns:
        队列统计信息
    """
    try:
        if not settings.queue_enabled:
            return success_response(
                data={
                    "enabled": False,
                    "queues": {}
                },
                message="消息队列未启用",
                request=request
            )
        
        qm = await get_queue_manager()
        stats = {}
        for task_type in TaskType:
            length = await qm.get_queue_length(task_type)
            stats[task_type.value] = {
                "queue_length": length
            }
        
        return success_response(
            data={
                "enabled": True,
                "queues": stats
            },
            message="获取队列统计成功",
            request=request
        )
    except Exception as e:
        logger.error(f"获取队列统计失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"获取队列统计失败: {str(e)}",
            request=request
        )

