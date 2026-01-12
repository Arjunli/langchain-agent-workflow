"""聊天 API"""
from fastapi import APIRouter, HTTPException
from app.models.message import ChatRequest, ChatResponse
from app.agents.chat_agent import ChatAgent
from app.agents.workflow_agent import WorkflowAgent
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.storage.knowledge_store import KnowledgeStore
from app.storage.prompt_store import PromptStore
from app.tools import tool_registry
from typing import AsyncGenerator
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 初始化组件（实际应用中应该使用依赖注入）
workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(workflow_registry, tool_registry)
knowledge_store = KnowledgeStore()
prompt_store = PromptStore()
workflow_agent = WorkflowAgent(workflow_engine, knowledge_store, prompt_store)
chat_agent = ChatAgent(workflow_agent)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """聊天接口"""
    try:
        result = await chat_agent.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            prompt_id=request.prompt_id
        )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            workflow_id=result.get("workflow_id"),
            workflow_status=result.get("workflow_status"),
            tool_calls=result.get("tool_calls", []),
            metadata={"prompt_id": result.get("prompt_id")}
        )
    
    except Exception as e:
        logger.error(f"聊天处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """流式聊天接口"""
    try:
        # TODO: 实现流式响应
        result = await chat_agent.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context
        )
        
        # 简单的流式响应（实际应该使用 Server-Sent Events）
        yield f"data: {result['response']}\n\n"
    
    except Exception as e:
        logger.error(f"流式聊天处理失败: {e}", exc_info=True)
        yield f"error: {str(e)}\n\n"

