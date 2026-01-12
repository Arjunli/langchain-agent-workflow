"""工作流管理 API"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from app.models.workflow import Workflow
from app.models.task import Task, TaskType, TaskStatus
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.tools import tool_registry
from app.queue.manager import QueueManager
from app.config import settings
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger, get_trace_id

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


@router.post("", response_model=Workflow)
async def create_workflow(workflow: Workflow) -> Workflow:
    """创建工作流"""
    try:
        workflow_engine.register_workflow(workflow)
        return workflow
    except Exception as e:
        logger.error(f"创建工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_workflow(file: UploadFile = File(...)) -> Workflow:
    """上传工作流文件（YAML/JSON）"""
    try:
        content = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        
        # 保存临时文件
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f'.{file_ext}') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            if file_ext == 'yaml' or file_ext == 'yml':
                workflow = workflow_registry.load_from_yaml(tmp_path)
            elif file_ext == 'json':
                workflow = workflow_registry.load_from_json(tmp_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
            
            workflow_engine.register_workflow(workflow)
            return workflow
        
        finally:
            os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"上传工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Workflow])
async def list_workflows() -> List[Workflow]:
    """列出所有工作流"""
    return workflow_engine.list_workflows()


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str) -> Workflow:
    """获取工作流"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")
    return workflow


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    variables: Dict[str, Any] = None,
    async_execute: bool = Query(default=True, description="是否异步执行")
) -> Dict[str, Any]:
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
            raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")
        
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
                
                return {
                    "task_id": task_id,
                    "status": "queued",
                    "message": "工作流已加入执行队列",
                    "workflow_id": workflow_id
                }
            except Exception as e:
                logger.warning(f"消息队列不可用，使用同步执行: {e}")
                # 降级到同步执行
                result = await workflow_engine.execute_workflow(workflow_id, variables)
                return {
                    "task_id": None,
                    "status": result.status.value,
                    "workflow": result.model_dump(),
                    "message": "工作流已同步执行完成"
                }
        else:
            # 同步执行
            result = await workflow_engine.execute_workflow(workflow_id, variables)
            return {
                "task_id": None,
                "status": result.status.value,
                "workflow": result.model_dump(),
                "message": "工作流已同步执行完成"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}", response_model=List[Workflow])
async def search_workflows(keyword: str) -> List[Workflow]:
    """搜索工作流"""
    return workflow_engine.search_workflows(keyword)


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
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
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        return {
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, Any]:
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
            raise HTTPException(status_code=400, detail="任务无法取消（可能已开始执行或不存在）")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "任务已取消"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/stats")
async def get_queue_stats() -> Dict[str, Any]:
    """
    获取队列统计信息
    
    Returns:
        队列统计信息
    """
    try:
        if not settings.queue_enabled:
            return {
                "enabled": False,
                "message": "消息队列未启用"
            }
        
        qm = await get_queue_manager()
        stats = {}
        for task_type in TaskType:
            length = await qm.get_queue_length(task_type)
            stats[task_type.value] = {
                "queue_length": length
            }
        
        return {
            "enabled": True,
            "queues": stats
        }
    except Exception as e:
        logger.error(f"获取队列统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

