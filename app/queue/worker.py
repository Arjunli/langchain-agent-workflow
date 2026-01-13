"""任务Worker"""
import asyncio
from typing import Optional, Callable, Dict, Any
from app.queue.manager import QueueManager
from app.models.task import Task, TaskType, TaskStatus
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.tools import tool_registry
from app.utils.logger import get_logger, set_trace_id, set_coroutine_id
import traceback

logger = get_logger(__name__)
worker_logger = get_logger("worker")


class TaskWorker:
    """任务Worker，处理队列中的任务"""
    
    def __init__(
        self,
        queue_manager: QueueManager,
        workflow_engine: Optional[WorkflowEngine] = None,
        max_workers: int = 5
    ):
        """
        初始化Worker
        
        Args:
            queue_manager: 队列管理器
            workflow_engine: 工作流引擎（可选）
            max_workers: 最大并发worker数
        """
        self.queue_manager = queue_manager
        self.workflow_engine = workflow_engine
        self.max_workers = max_workers
        self.running = False
        self.workers: Dict[TaskType, asyncio.Task] = {}
        self.task_handlers: Dict[TaskType, Callable] = {
            TaskType.WORKFLOW_EXECUTE: self._handle_workflow_task,
            TaskType.CHAT_PROCESS: self._handle_chat_task,
            TaskType.KNOWLEDGE_SEARCH: self._handle_knowledge_task,
        }
    
    async def start(self):
        """启动Worker"""
        if self.running:
            logger.warning("Worker已经在运行中")
            return
        
        await self.queue_manager.connect()
        self.running = True
        
        # 为每种任务类型启动worker
        for task_type in TaskType:
            if task_type in self.task_handlers:
                worker_task = asyncio.create_task(
                    self._worker_loop(task_type)
                )
                self.workers[task_type] = worker_task
                logger.info(f"Worker已启动: {task_type.value}")
    
    async def stop(self):
        """停止Worker"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待所有worker完成当前任务
        for task_type, worker_task in self.workers.items():
            logger.info(f"正在停止Worker: {task_type.value}")
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        
        self.workers.clear()
        
        # 确保断开连接（即使之前出错也要执行）
        try:
            await self.queue_manager.disconnect()
        except Exception as e:
            logger.warning(f"断开队列管理器连接失败: {e}")
        
        logger.info("所有Worker已停止")
    
    async def _worker_loop(self, task_type: TaskType):
        """Worker主循环"""
        worker_logger.info(f"Worker循环已启动: {task_type.value}")
        
        # 设置协程ID
        coroutine_id = f"worker_{task_type.value}_{id(asyncio.current_task())}"
        set_coroutine_id(coroutine_id)
        
        while self.running:
            try:
                # 从队列中取出任务
                task = await self.queue_manager.dequeue_task(task_type, timeout=1)
                
                if not task:
                    continue
                
                # 设置任务的trace_id（如果有）
                if task.metadata.get("trace_id"):
                    set_trace_id(task.metadata["trace_id"])
                
                # 检查任务是否已取消
                if task.status == TaskStatus.CANCELLED:
                    worker_logger.info(f"任务已取消，跳过: {task.id}")
                    continue
                
                # 处理任务
                handler = self.task_handlers.get(task_type)
                if handler:
                    await self._process_task(task, handler)
                else:
                    worker_logger.warning(f"未找到任务处理器: {task_type.value}")
                    await self.queue_manager.complete_task(
                        task.id,
                        error=f"未找到任务处理器: {task_type.value}"
                    )
            
            except asyncio.CancelledError:
                worker_logger.info(f"Worker循环已取消: {task_type.value}")
                break
            except Exception as e:
                worker_logger.error(f"Worker循环错误: {e}", exc_info=True)
                await asyncio.sleep(1)  # 避免错误循环
    
    async def _process_task(self, task: Task, handler: Callable):
        """
        处理任务
        
        Args:
            task: 任务对象
            handler: 任务处理函数
        """
        try:
            worker_logger.info(
                f"开始处理任务: {task.id}, 类型: {task.type.value}",
                extra={"task_id": task.id, "task_type": task.type.value}
            )
            
            # 调用处理器
            result = await handler(task)
            
            # 完成任务
            await self.queue_manager.complete_task(task.id, result=result)
            
            worker_logger.info(
                f"任务处理完成: {task.id}",
                extra={"task_id": task.id, "task_type": task.type.value}
            )
        
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            worker_logger.error(
                f"任务处理失败: {task.id}, 错误: {error_msg}",
                extra={"task_id": task.id, "task_type": task.type.value, "error": error_msg},
                exc_info=True
            )
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.QUEUED
                task.error = None
                await self.queue_manager.update_task(task)
                
                # 重新入队
                await self.queue_manager.enqueue_task(task)
                worker_logger.info(
                    f"任务将重试: {task.id}, 重试次数: {task.retry_count}/{task.max_retries}",
                    extra={"task_id": task.id, "retry_count": task.retry_count}
                )
            else:
                # 重试次数用尽，标记为失败
                await self.queue_manager.complete_task(
                    task.id,
                    error=f"{error_msg}\n{error_trace}"
                )
    
    async def _handle_workflow_task(self, task: Task) -> Any:
        """
        处理工作流执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            任务结果
        """
        if not self.workflow_engine:
            raise ValueError("工作流引擎未配置")
        
        workflow_id = task.params.get("workflow_id")
        variables = task.params.get("variables", {})
        
        if not workflow_id:
            raise ValueError("工作流ID不能为空")
        
        # 执行工作流
        result = await self.workflow_engine.execute_workflow(workflow_id, variables)
        
        return {
            "workflow_id": result.id,
            "status": result.status.value,
            "variables": result.variables,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None
        }
    
    async def _handle_chat_task(self, task: Task) -> Any:
        """
        处理聊天任务
        
        Args:
            task: 任务对象
            
        Returns:
            任务结果
        """
        # TODO: 实现聊天任务处理
        # 这里需要注入ChatAgent
        raise NotImplementedError("聊天任务处理尚未实现")
    
    async def _handle_knowledge_task(self, task: Task) -> Any:
        """
        处理知识库搜索任务
        
        Args:
            task: 任务对象
            
        Returns:
            任务结果
        """
        # TODO: 实现知识库搜索任务处理
        raise NotImplementedError("知识库搜索任务处理尚未实现")

