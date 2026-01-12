"""Prompt 管理 API"""
from fastapi import APIRouter, HTTPException
from app.models.prompt import PromptTemplate, PromptUsage, PromptType
from app.storage.prompt_store import PromptStore
from typing import List, Optional, Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 初始化 Prompt 存储
prompt_store = PromptStore()


@router.post("/prompts", response_model=PromptTemplate)
async def create_prompt(prompt: PromptTemplate) -> PromptTemplate:
    """创建 Prompt"""
    try:
        result = prompt_store.create_prompt(prompt)
        return result
    except Exception as e:
        logger.error(f"创建 Prompt 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts", response_model=List[PromptTemplate])
async def list_prompts(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    active_only: bool = True
) -> List[PromptTemplate]:
    """列出所有 Prompt"""
    tag_list = tags.split(",") if tags else None
    return prompt_store.list_prompts(
        category=category,
        tags=tag_list,
        active_only=active_only
    )


@router.get("/prompts/{prompt_id}", response_model=PromptTemplate)
async def get_prompt(prompt_id: str) -> PromptTemplate:
    """获取 Prompt"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt 不存在: {prompt_id}")
    return prompt


@router.get("/prompts/default/{category}", response_model=PromptTemplate)
async def get_default_prompt(category: Optional[str] = None) -> PromptTemplate:
    """获取默认 Prompt"""
    prompt = prompt_store.get_default_prompt(category=category)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"未找到默认 Prompt（分类: {category}）")
    return prompt


@router.put("/prompts/{prompt_id}", response_model=PromptTemplate)
async def update_prompt(
    prompt_id: str,
    update_data: Dict[str, Any]
) -> PromptTemplate:
    """更新 Prompt"""
    prompt = prompt_store.update_prompt(prompt_id, **update_data)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt 不存在: {prompt_id}")
    return prompt


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str) -> dict:
    """删除 Prompt"""
    success = prompt_store.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Prompt 不存在: {prompt_id}")
    return {"success": True, "message": f"Prompt {prompt_id} 已删除"}


@router.post("/prompts/{prompt_id}/render")
async def render_prompt(
    prompt_id: str,
    variables: Dict[str, Any]
) -> dict:
    """渲染 Prompt（替换变量）"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt 不存在: {prompt_id}")
    
    try:
        rendered = prompt.render(**variables)
        return {
            "prompt_id": prompt_id,
            "rendered_content": rendered,
            "variables_used": variables
        }
    except Exception as e:
        logger.error(f"渲染 Prompt 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}/usage", response_model=List[PromptUsage])
async def get_prompt_usage(
    prompt_id: str,
    limit: int = 100
) -> List[PromptUsage]:
    """获取 Prompt 使用历史"""
    return prompt_store.get_usage_history(prompt_id=prompt_id, limit=limit)


@router.get("/prompts/search/{keyword}", response_model=List[PromptTemplate])
async def search_prompts(keyword: str) -> List[PromptTemplate]:
    """搜索 Prompt"""
    return prompt_store.search_prompts(keyword)

