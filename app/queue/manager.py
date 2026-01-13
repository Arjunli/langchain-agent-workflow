"""消息队列管理器"""
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any
from app.models.task import Task, TaskStatus, TaskType
from app.config import settings
from app.utils.logger import get_logger
from datetime import datetime
import asyncio

logger = get_logger(__name__)


class QueueManager:
    """消息队列管理器（基于Redis，使用连接池）"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化队列管理器
        
        Args:
            redis_url: Redis连接URL，格式: redis://localhost:6379/0
        """
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self.redis_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self._queue_prefix = "task_queue:"
        self._task_prefix = "task:"
        self._status_prefix = "task_status:"
        self._connected = False
    
    async def connect(self):
        """连接Redis（使用连接池）"""
        if self._connected and self.redis_client:
            # 检查连接是否健康
            try:
                await self.redis_client.ping()
                return
            except Exception:
                logger.warning("Redis连接不健康，重新连接")
                await self.disconnect()
        
        try:
            # 创建连接池
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,  # 最大连接数
                retry_on_timeout=True
            )
            
            # 创建Redis客户端（使用连接池）
            self.redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            await self.redis_client.ping()
            self._connected = True
            logger.info("Redis连接成功（使用连接池）")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        self._connected = False
        
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.debug("Redis客户端已关闭")
            except Exception as e:
                logger.warning(f"关闭Redis客户端失败: {e}")
            finally:
                self.redis_client = None
        
        if self._connection_pool:
            try:
                await self._connection_pool.disconnect()
                logger.debug("Redis连接池已关闭")
            except Exception as e:
                logger.warning(f"关闭Redis连接池失败: {e}")
            finally:
                self._connection_pool = None
        
        logger.info("Redis连接已关闭")
    
    async def _ensure_connected(self):
        """确保连接存在且健康"""
        if not self._connected or not self.redis_client:
            await self.connect()
        else:
            try:
                await self.redis_client.ping()
            except Exception:
                logger.warning("Redis连接不健康，重新连接")
                await self.disconnect()
                await self.connect()
    
    def _get_queue_name(self, task_type: TaskType) -> str:
        """获取队列名称"""
        return f"{self._queue_prefix}{task_type.value}"
    
    def _get_task_key(self, task_id: str) -> str:
        """获取任务存储键"""
        return f"{self._task_prefix}{task_id}"
    
    def _get_status_key(self, task_id: str) -> str:
        """获取任务状态键"""
        return f"{self._status_prefix}{task_id}"
    
    async def enqueue_task(self, task: Task) -> str:
        """
        将任务加入队列
        
        Args:
            task: 任务对象
            
        Returns:
            任务ID
        """
        await self._ensure_connected()
        
        # 更新任务状态和时间戳
        task.status = TaskStatus.QUEUED
        task.updated_at = datetime.now()
        
        # 序列化任务
        task_data = task.model_dump_json()
        
        # 存储任务详情
        task_key = self._get_task_key(task.id)
        await self.redis_client.setex(
            task_key,
            86400 * 7,  # 7天过期
            task_data
        )
        
        # 更新任务状态
        status_key = self._get_status_key(task.id)
        await self.redis_client.setex(
            status_key,
            86400 * 7,
            task.status.value
        )
        
        # 将任务加入队列（使用LPUSH）
        queue_name = self._get_queue_name(task.type)
        await self.redis_client.lpush(queue_name, task.id)
        
        logger.info(f"任务已入队: {task.id}, 类型: {task.type.value}")
        return task.id
    
    async def dequeue_task(self, task_type: TaskType, timeout: int = 5) -> Optional[Task]:
        """
        从队列中取出任务（阻塞式）
        
        Args:
            task_type: 任务类型
            timeout: 超时时间（秒）
            
        Returns:
            任务对象，如果超时则返回None
        """
        await self._ensure_connected()
        
        queue_name = self._get_queue_name(task_type)
        
        # 使用BRPOP阻塞式取出任务
        result = await self.redis_client.brpop(queue_name, timeout=timeout)
        
        if not result:
            return None
        
        _, task_id = result
        
        # 获取任务详情
        task_key = self._get_task_key(task_id)
        task_data = await self.redis_client.get(task_key)
        
        if not task_data:
            logger.warning(f"任务数据不存在: {task_id}")
            return None
        
        # 反序列化任务
        task_dict = json.loads(task_data)
        task = Task(**task_dict)
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.updated_at = datetime.now()
        
        # 保存更新后的任务
        await self.update_task(task)
        
        logger.info(f"任务已出队: {task.id}, 类型: {task.type.value}")
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        await self._ensure_connected()
        
        task_key = self._get_task_key(task_id)
        task_data = await self.redis_client.get(task_key)
        
        if not task_data:
            return None
        
        task_dict = json.loads(task_data)
        return Task(**task_dict)
    
    async def update_task(self, task: Task):
        """
        更新任务状态
        
        Args:
            task: 任务对象
        """
        await self._ensure_connected()
        
        task.updated_at = datetime.now()
        
        # 序列化任务
        task_data = task.model_dump_json()
        
        # 更新任务详情
        task_key = self._get_task_key(task.id)
        await self.redis_client.setex(
            task_key,
            86400 * 7,  # 7天过期
            task_data
        )
        
        # 更新任务状态
        status_key = self._get_status_key(task.id)
        await self.redis_client.setex(
            status_key,
            86400 * 7,
            task.status.value
        )
        
        logger.debug(f"任务状态已更新: {task.id}, 状态: {task.status.value}")
    
    async def complete_task(self, task_id: str, result: Any = None, error: Optional[str] = None):
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
            error: 错误信息（如果有）
        """
        task = await self.get_task(task_id)
        if not task:
            logger.warning(f"任务不存在: {task_id}")
            return
        
        task.completed_at = datetime.now()
        task.result = result
        task.error = error
        
        if error:
            task.status = TaskStatus.FAILED
        else:
            task.status = TaskStatus.COMPLETED
        
        await self.update_task(task)
        logger.info(f"任务已完成: {task_id}, 状态: {task.status.value}")
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态，如果不存在则返回None
        """
        await self._ensure_connected()
        
        status_key = self._get_status_key(task_id)
        status_str = await self.redis_client.get(status_key)
        
        if not status_str:
            return None
        
        try:
            return TaskStatus(status_str)
        except ValueError:
            return None
    
    async def get_queue_length(self, task_type: TaskType) -> int:
        """
        获取队列长度
        
        Args:
            task_type: 任务类型
            
        Returns:
            队列长度
        """
        await self._ensure_connected()
        
        queue_name = self._get_queue_name(task_type)
        return await self.redis_client.llen(queue_name)
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（如果任务还在队列中）
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # 只能取消待处理或已入队的任务
        if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        await self.update_task(task)
        
        logger.info(f"任务已取消: {task_id}")
        return True

