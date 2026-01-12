"""聊天 Agent"""
from typing import Dict, Any, Optional, List
from app.agents.workflow_agent import WorkflowAgent
from app.models.message import Message, Conversation
from app.models.agent import AgentState
import uuid
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatAgent:
    """聊天 Agent，管理对话状态和消息历史"""
    
    def __init__(self, workflow_agent: WorkflowAgent):
        self.workflow_agent = workflow_agent
        self._conversations: Dict[str, Conversation] = {}
        self._agent_states: Dict[str, AgentState] = {}
    
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
        prompt_id: Optional[str] = None
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
            "prompt_id": prompt_id or response.metadata.get("prompt_id")
        }

