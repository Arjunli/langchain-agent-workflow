"""WebSocket 支持"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.agents.chat_agent import ChatAgent
from app.agents.workflow_agent import WorkflowAgent
from app.workflows.engine import WorkflowEngine
from app.storage.knowledge_store import KnowledgeStore
from app.storage.prompt_store import PromptStore
from app.tools import tool_registry
from app.workflows.registry import WorkflowRegistry
import json
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
    """WebSocket 聊天接口"""
    await websocket.accept()
    conversation_id = None
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
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
    
    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 处理失败: {e}", exc_info=True)
        await websocket.send_text(json.dumps({"error": str(e)}))

