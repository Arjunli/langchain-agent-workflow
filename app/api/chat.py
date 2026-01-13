"""聊天 API"""
from fastapi import APIRouter, HTTPException, Request
from app.models.message import ChatRequest, ChatResponse
from app.models.response import BaseResponse
from app.utils.response import success_response, internal_error_response
from app.agents.chat_agent import ChatAgent
from app.agents.workflow_agent import WorkflowAgent
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.storage.knowledge_store import KnowledgeStore
from app.storage.prompt_store import PromptStore
from app.tools import tool_registry
from typing import AsyncGenerator
from app.utils.logger import get_logger
import json
import asyncio
import uuid

logger = get_logger(__name__)

router = APIRouter()

# 初始化组件（实际应用中应该使用依赖注入）
workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(workflow_registry, tool_registry)
knowledge_store = KnowledgeStore()
prompt_store = PromptStore()
workflow_agent = WorkflowAgent(workflow_engine, knowledge_store, prompt_store)
chat_agent = ChatAgent(workflow_agent)


@router.post("", response_model=BaseResponse[ChatResponse])
async def chat(request_body: ChatRequest, request: Request) -> BaseResponse[ChatResponse]:
    """聊天接口"""
    try:
        result = await chat_agent.chat(
            message=request_body.message,
            conversation_id=request_body.conversation_id,
            context=request_body.context,
            prompt_id=request_body.prompt_id
        )
        
        chat_response = ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            workflow_id=result.get("workflow_id"),
            workflow_status=result.get("workflow_status"),
            tool_calls=result.get("tool_calls", []),
            metadata={"prompt_id": result.get("prompt_id")}
        )
        
        return success_response(
            data=chat_response,
            message="聊天处理成功",
            request=request
        )
    
    except Exception as e:
        logger.error(f"聊天处理失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"聊天处理失败: {str(e)}",
            request=request
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    流式聊天接口（Server-Sent Events）
    
    支持：
    - 流式响应
    - 中断恢复（返回部分响应）
    - 自动重试
    """
    from app.utils.llm_response import get_response_handler
    
    response_id = str(uuid.uuid4())
    response_handler = get_response_handler()
    
    try:
        # 使用流式处理
        result = await chat_agent.chat_stream(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context,
            prompt_id=request.prompt_id,
            response_id=response_id
        )
        
        # 发送流式响应（Server-Sent Events格式）
        buffer = response_handler.get_buffer(response_id)
        if buffer:
            # 如果缓冲区有内容，逐块发送
            content = buffer.get_content()
            chunk_size = 50  # 每次发送50个字符
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'response_id': response_id})}\n\n"
            
            # 发送完成标记
            yield f"data: {json.dumps({'done': True, 'response_id': response_id, 'complete': buffer.complete})}\n\n"
        else:
            # 如果没有缓冲区，发送完整响应
            yield f"data: {json.dumps({'chunk': result.get('response', ''), 'response_id': response_id, 'done': True})}\n\n"
    
    except asyncio.CancelledError:
        logger.warning(f"流式响应被取消: {response_id}")
        # 尝试返回部分响应
        buffer = response_handler.get_buffer(response_id)
        if buffer and buffer.get_partial_content():
            yield f"data: {json.dumps({'chunk': buffer.get_partial_content(), 'response_id': response_id, 'partial': True, 'done': True})}\n\n"
        else:
            yield f"data: {json.dumps({'error': '请求被取消', 'response_id': response_id, 'done': True})}\n\n"
    
    except Exception as e:
        logger.error(f"流式聊天处理失败: {e}", exc_info=True)
        # 尝试返回部分响应
        buffer = response_handler.get_buffer(response_id)
        if buffer and buffer.get_partial_content():
            yield f"data: {json.dumps({'chunk': buffer.get_partial_content(), 'response_id': response_id, 'partial': True, 'error': str(e), 'done': True})}\n\n"
        else:
            yield f"data: {json.dumps({'error': str(e), 'response_id': response_id, 'done': True})}\n\n"
    
    finally:
        # 清理缓冲区（延迟清理，给客户端时间接收）
        await asyncio.sleep(5)
        response_handler.cleanup_buffer(response_id)

