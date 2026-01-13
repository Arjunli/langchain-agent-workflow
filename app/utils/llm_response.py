"""LLM响应处理工具 - 处理流式响应、中断恢复、重试等"""
import asyncio
from typing import AsyncIterator, Optional, Dict, Any, List
from datetime import datetime
from app.utils.logger import get_logger
from app.config import settings
import json

logger = get_logger(__name__)


class StreamResponseBuffer:
    """流式响应缓冲区 - 保存中间结果，防止中断丢失数据"""
    
    def __init__(self, response_id: str, conversation_id: Optional[str] = None):
        """
        初始化流式响应缓冲区
        
        Args:
            response_id: 响应ID（用于追踪）
            conversation_id: 对话ID（可选）
        """
        self.response_id = response_id
        self.conversation_id = conversation_id
        self.buffer: List[str] = []
        self.complete = False
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def append(self, chunk: str) -> None:
        """追加数据块"""
        self.buffer.append(chunk)
        self.updated_at = datetime.now()
    
    def get_content(self) -> str:
        """获取完整内容"""
        return "".join(self.buffer)
    
    def get_partial_content(self) -> str:
        """获取部分内容（用于中断恢复）"""
        return "".join(self.buffer)
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self.complete = True
        self.updated_at = datetime.now()
    
    def mark_error(self, error: str) -> None:
        """标记为错误"""
        self.error = error
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于持久化）"""
        return {
            "response_id": self.response_id,
            "conversation_id": self.conversation_id,
            "content": self.get_content(),
            "complete": self.complete,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


class LLMResponseHandler:
    """LLM响应处理器 - 处理流式响应、重试、错误恢复"""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        save_partial: bool = True
    ):
        """
        初始化LLM响应处理器
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            save_partial: 是否保存部分响应
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.save_partial = save_partial
        self._buffers: Dict[str, StreamResponseBuffer] = {}
    
    def create_buffer(self, response_id: str, conversation_id: Optional[str] = None) -> StreamResponseBuffer:
        """创建响应缓冲区"""
        buffer = StreamResponseBuffer(response_id, conversation_id)
        self._buffers[response_id] = buffer
        logger.debug(f"创建响应缓冲区: {response_id}")
        return buffer
    
    def get_buffer(self, response_id: str) -> Optional[StreamResponseBuffer]:
        """获取响应缓冲区"""
        return self._buffers.get(response_id)
    
    async def process_stream(
        self,
        stream: AsyncIterator[str],
        response_id: str,
        conversation_id: Optional[str] = None,
        on_chunk: Optional[callable] = None
    ) -> StreamResponseBuffer:
        """
        处理流式响应
        
        Args:
            stream: 流式响应迭代器
            response_id: 响应ID
            conversation_id: 对话ID
            on_chunk: 每个数据块的回调函数
        
        Returns:
            响应缓冲区
        """
        buffer = self.create_buffer(response_id, conversation_id)
        
        try:
            async for chunk in stream:
                buffer.append(chunk)
                
                # 调用回调函数
                if on_chunk:
                    try:
                        await on_chunk(chunk, buffer)
                    except Exception as e:
                        logger.warning(f"处理数据块回调失败: {e}")
            
            buffer.mark_complete()
            logger.info(f"流式响应完成: {response_id}, 长度: {len(buffer.get_content())}")
            
        except asyncio.CancelledError:
            logger.warning(f"流式响应被取消: {response_id}")
            buffer.mark_error("cancelled")
            raise
        except Exception as e:
            logger.error(f"流式响应处理失败: {response_id}, 错误: {e}", exc_info=True)
            buffer.mark_error(str(e))
            raise
        
        return buffer
    
    async def process_with_retry(
        self,
        stream_func: callable,
        response_id: str,
        conversation_id: Optional[str] = None,
        on_chunk: Optional[callable] = None
    ) -> StreamResponseBuffer:
        """
        带重试的流式响应处理
        
        Args:
            stream_func: 返回流式响应的函数
            response_id: 响应ID
            conversation_id: 对话ID
            on_chunk: 每个数据块的回调函数
        
        Returns:
            响应缓冲区
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 如果是重试，尝试恢复之前的缓冲区
                buffer = self.get_buffer(response_id)
                if buffer and buffer.get_partial_content():
                    logger.info(f"尝试恢复响应: {response_id}, 已有内容长度: {len(buffer.get_partial_content())}")
                
                # 创建新的流
                stream = await stream_func()
                
                # 处理流
                buffer = await self.process_stream(
                    stream,
                    response_id,
                    conversation_id,
                    on_chunk
                )
                
                return buffer
                
            except Exception as e:
                last_error = e
                logger.warning(f"流式响应处理失败 (尝试 {attempt + 1}/{self.max_retries}): {response_id}, 错误: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    # 最后一次尝试失败
                    buffer = self.get_buffer(response_id)
                    if buffer:
                        buffer.mark_error(str(e))
                    raise
        
        # 如果所有重试都失败，返回部分结果（如果有）
        buffer = self.get_buffer(response_id)
        if buffer and self.save_partial:
            logger.info(f"返回部分响应: {response_id}, 内容长度: {len(buffer.get_partial_content())}")
            return buffer
        
        raise last_error
    
    def get_partial_response(self, response_id: str) -> Optional[str]:
        """获取部分响应（用于中断恢复）"""
        buffer = self.get_buffer(response_id)
        if buffer:
            return buffer.get_partial_content()
        return None
    
    def cleanup_buffer(self, response_id: str) -> None:
        """清理缓冲区"""
        if response_id in self._buffers:
            del self._buffers[response_id]
            logger.debug(f"清理响应缓冲区: {response_id}")
    
    def cleanup_old_buffers(self, max_age_seconds: int = 3600) -> int:
        """清理旧的缓冲区"""
        current_time = datetime.now()
        old_buffers = []
        
        for response_id, buffer in self._buffers.items():
            age = (current_time - buffer.updated_at).total_seconds()
            if age > max_age_seconds:
                old_buffers.append(response_id)
        
        for response_id in old_buffers:
            self.cleanup_buffer(response_id)
        
        if old_buffers:
            logger.info(f"清理了 {len(old_buffers)} 个旧缓冲区")
        
        return len(old_buffers)


# 全局响应处理器实例
_response_handler = LLMResponseHandler(
    max_retries=getattr(settings, 'llm_max_retries', 3),
    retry_delay=getattr(settings, 'llm_retry_delay', 1.0),
    save_partial=True
)


def get_response_handler() -> LLMResponseHandler:
    """获取全局响应处理器"""
    return _response_handler
