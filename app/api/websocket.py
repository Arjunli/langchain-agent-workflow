"""WebSocket 支持"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.agents.chat_agent import ChatAgent
from app.agents.workflow_agent import WorkflowAgent
from app.workflows.engine import WorkflowEngine
from app.storage.knowledge_store import KnowledgeStore
from app.storage.prompt_store import PromptStore
from app.tools import tool_registry
from app.workflows.registry import WorkflowRegistry
from app.config import settings
import json
import asyncio
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 初始化组件
workflow_registry = WorkflowRegistry()
workflow_engine = WorkflowEngine(workflow_registry, tool_registry)
knowledge_store = KnowledgeStore()
prompt_store = PromptStore()
workflow_agent = WorkflowAgent(workflow_engine, knowledge_store, prompt_store)
chat_agent = ChatAgent(workflow_agent)


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天接口（带超时和资源清理）"""
    connection_id = f"ws_{datetime.now().timestamp()}"
    conversation_id = None
    connected = False
    
    try:
        await websocket.accept()
        connected = True
        logger.info(f"WebSocket连接已建立: {connection_id}")
        
        # 设置接收消息超时
        while True:
            try:
                # 使用asyncio.wait_for设置超时
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.websocket_timeout
                )
                
                message_data = json.loads(data)
                message = message_data.get("message", "")
                conversation_id = message_data.get("conversation_id", conversation_id)
                
                # 处理消息
                result = await chat_agent.chat(
                    message=message,
                    conversation_id=conversation_id
                )
                
                # 发送响应
                await websocket.send_text(json.dumps({
                    "conversation_id": result["conversation_id"],
                    "response": result["response"],
                    "workflow_id": result.get("workflow_id"),
                    "workflow_status": result.get("workflow_status")
                }))
            
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket接收消息超时: {connection_id}")
                await websocket.send_text(json.dumps({
                    "error": "接收消息超时，连接将关闭"
                }))
                break
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket客户端断开连接: {connection_id}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket处理失败: {connection_id}, 错误: {e}", exc_info=True)
        if connected:
            try:
                await websocket.send_text(json.dumps({"error": str(e)}))
            except Exception:
                pass  # 连接可能已断开
    
    finally:
        # 确保资源清理
        if connected:
            try:
                await websocket.close()
                logger.info(f"WebSocket连接已关闭: {connection_id}")
            except Exception as e:
                logger.warning(f"关闭WebSocket连接失败: {connection_id}, 错误: {e}")

