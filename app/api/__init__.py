"""API 路由"""
from fastapi import APIRouter

api_router = APIRouter(prefix="/api", tags=["api"])

# 导入路由
from . import chat, workflow, websocket, knowledge, prompt

# 注册路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(workflow.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(prompt.router, tags=["prompts"])

