"""聊天 Agent"""
from typing import Dict, Any, Optional, List
from app.agents.workflow_agent import WorkflowAgent
from app.models.message import Message, Conversation
from app.models.agent import AgentState
from app.utils.cache import LRUTTLCache
from app.config import settings
import uuid
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatAgent:
    """聊天 Agent，管理对话状态和消息历史"""
    
    def __init__(self, workflow_agent: WorkflowAgent):
        self.workflow_agent = workflow_agent
        # 使用LRU+TTL缓存限制内存使用
        self._conversations = LRUTTLCache(
            max_size=settings.max_conversations,
            default_ttl=settings.conversation_ttl
        )
        self._agent_states = LRUTTLCache(
            max_size=settings.max_conversations,
            default_ttl=settings.conversation_ttl
        )
    
    def create_conversation(self) -> Conversation:
        """创建新对话"""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(id=conversation_id)
        self._conversations[conversation_id] = conversation
        
        # 创建 Agent 状态
        agent_state = AgentState(conversation_id=conversation_id)
        self._agent_states[conversation_id] = agent_state
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        return self._conversations.get(conversation_id)
    
    def cleanup_expired(self) -> int:
        """
        清理过期的对话和状态
        
        Returns:
            清理的数量
        """
        conversations_cleaned = self._conversations.cleanup_expired()
        states_cleaned = self._agent_states.cleanup_expired()
        total_cleaned = conversations_cleaned + states_cleaned
        
        if total_cleaned > 0:
            logger.info(f"清理了 {total_cleaned} 个过期对话和状态")
        
        return total_cleaned
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "conversations": {
                "size": self._conversations.size(),
                "max_size": settings.max_conversations,
                "ttl": settings.conversation_ttl
            },
            "agent_states": {
                "size": self._agent_states.size(),
                "max_size": settings.max_conversations,
                "ttl": settings.conversation_ttl
            }
        }
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        """添加消息"""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            conversation = self.create_conversation()
        
        message = Message(role=role, content=content)
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        return message
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """处理聊天消息"""
        # 获取或创建对话
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                conversation = self.create_conversation()
                conversation_id = conversation.id
        else:
            conversation = self.create_conversation()
            conversation_id = conversation.id
        
        # 添加用户消息
        self.add_message(conversation_id, "user", message)
        
        # 获取 Agent 状态
        agent_state = self._agent_states.get(conversation_id)
        if not agent_state:
            agent_state = AgentState(conversation_id=conversation_id)
            self._agent_states[conversation_id] = agent_state
        
        # 构建上下文（包含对话历史）
        chat_context = context or {}
        chat_context["conversation_history"] = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages[-10:]  # 最近10条消息
        ]
        chat_context["conversation_id"] = conversation_id
        
        # 调用工作流 Agent（传递 prompt_id）
        if stream:
            response = await self.workflow_agent.process_message_stream(
                message, chat_context, prompt_id=prompt_id
            )
        else:
            response = await self.workflow_agent.process_message(message, chat_context, prompt_id=prompt_id)
        
        # 更新 Agent 状态
        agent_state.updated_at = datetime.now()
        if response.workflow_triggered and response.workflow_id:
            agent_state.current_workflow_id = response.workflow_id
            agent_state.workflow_history.append(response.workflow_id)
        agent_state.tool_calls.extend(response.tool_calls)
        
        # 添加助手消息
        self.add_message(conversation_id, "assistant", response.message)
        
        return {
            "conversation_id": conversation_id,
            "response": response.message,
            "workflow_id": response.workflow_id,
            "workflow_status": response.workflow_status,
            "tool_calls": response.tool_calls,
            "prompt_id": prompt_id or response.metadata.get("prompt_id"),
            "partial": response.metadata.get("partial", False),
            "response_id": response.metadata.get("response_id")
        }
    
    async def chat_stream(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[str] = None,
        response_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        流式聊天接口
        
        Args:
            message: 用户消息
            conversation_id: 对话ID
            context: 上下文信息
            prompt_id: Prompt ID
            response_id: 响应ID（用于追踪）
        
        Returns:
            聊天结果（包含部分响应支持）
        """
        # 获取或创建对话
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                conversation = self.create_conversation()
                conversation_id = conversation.id
        else:
            conversation = self.create_conversation()
            conversation_id = conversation.id
        
        # 添加用户消息
        self.add_message(conversation_id, "user", message)
        
        # 获取 Agent 状态
        agent_state = self._agent_states.get(conversation_id)
        if not agent_state:
            agent_state = AgentState(conversation_id=conversation_id)
            self._agent_states.set(conversation_id, agent_state)
        
        # 构建上下文（包含对话历史）
        chat_context = context or {}
        chat_context["conversation_history"] = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages[-10:]  # 最近10条消息
        ]
        chat_context["conversation_id"] = conversation_id
        
        # 调用工作流 Agent（流式）
        response = await self.workflow_agent.process_message_stream(
            message, chat_context, prompt_id=prompt_id, response_id=response_id
        )
        
        # 更新 Agent 状态
        agent_state.updated_at = datetime.now()
        if response.workflow_triggered and response.workflow_id:
            agent_state.current_workflow_id = response.workflow_id
            agent_state.workflow_history.append(response.workflow_id)
        agent_state.tool_calls.extend(response.tool_calls)
        
        # 添加助手消息（即使是部分响应也保存）
        self.add_message(conversation_id, "assistant", response.message)
        
        return {
            "conversation_id": conversation_id,
            "response": response.message,
            "workflow_id": response.workflow_id,
            "workflow_status": response.workflow_status,
            "tool_calls": response.tool_calls,
            "prompt_id": prompt_id or response.metadata.get("prompt_id"),
            "partial": response.metadata.get("partial", False),
            "response_id": response.metadata.get("response_id")
        }

