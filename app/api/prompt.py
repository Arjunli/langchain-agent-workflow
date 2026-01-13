"""Prompt 管理 API"""
from fastapi import APIRouter, HTTPException, Request
from app.models.prompt import PromptTemplate, PromptUsage, PromptType
from app.models.response import BaseResponse
from app.utils.response import (
    success_response,
    created_response,
    not_found_response,
    internal_error_response
)
from app.storage.prompt_store import PromptStore
from typing import List, Optional, Dict, Any
import uuid
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 初始化 Prompt 存储
prompt_store = PromptStore()


@router.post("/prompts", response_model=BaseResponse[PromptTemplate])
async def create_prompt(prompt: PromptTemplate, request: Request) -> BaseResponse[PromptTemplate]:
    """创建 Prompt"""
    try:
        result = prompt_store.create_prompt(prompt)
        return created_response(
            data=result,
            message="Prompt创建成功",
            request=request
        )
    except Exception as e:
        logger.error(f"创建 Prompt 失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"创建 Prompt 失败: {str(e)}",
            request=request
        )


@router.get("/prompts", response_model=BaseResponse[List[PromptTemplate]])
async def list_prompts(
    request: Request,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    active_only: bool = True
) -> BaseResponse[List[PromptTemplate]]:
    """列出所有 Prompt"""
    tag_list = tags.split(",") if tags else None
    prompts = prompt_store.list_prompts(
        category=category,
        tags=tag_list,
        active_only=active_only
    )
    return success_response(
        data=prompts,
        message=f"获取到 {len(prompts)} 个Prompt",
        request=request
    )


@router.get("/prompts/{prompt_id}", response_model=BaseResponse[PromptTemplate])
async def get_prompt(prompt_id: str, request: Request) -> BaseResponse[PromptTemplate]:
    """获取 Prompt"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return not_found_response(
            resource=f"Prompt {prompt_id}",
            request=request
        )
    return success_response(
        data=prompt,
        message="获取Prompt成功",
        request=request
    )


@router.get("/prompts/default/{category}", response_model=BaseResponse[PromptTemplate])
async def get_default_prompt(request: Request, category: Optional[str] = None) -> BaseResponse[PromptTemplate]:
    """获取默认 Prompt"""
    prompt = prompt_store.get_default_prompt(category=category)
    if not prompt:
        return not_found_response(
            resource=f"默认 Prompt（分类: {category}）",
            request=request
        )
    return success_response(
        data=prompt,
        message="获取默认Prompt成功",
        request=request
    )


@router.put("/prompts/{prompt_id}", response_model=BaseResponse[PromptTemplate])
async def update_prompt(
    prompt_id: str,
    update_data: Dict[str, Any],
    request: Request
) -> BaseResponse[PromptTemplate]:
    """更新 Prompt"""
    prompt = prompt_store.update_prompt(prompt_id, **update_data)
    if not prompt:
        return not_found_response(
            resource=f"Prompt {prompt_id}",
            request=request
        )
    return success_response(
        data=prompt,
        message="Prompt更新成功",
        request=request
    )


@router.delete("/prompts/{prompt_id}", response_model=BaseResponse[Dict[str, Any]])
async def delete_prompt(prompt_id: str, request: Request) -> BaseResponse[Dict[str, Any]]:
    """删除 Prompt"""
    success = prompt_store.delete_prompt(prompt_id)
    if not success:
        return not_found_response(
            resource=f"Prompt {prompt_id}",
            request=request
        )
    return success_response(
        data={"prompt_id": prompt_id},
        message=f"Prompt {prompt_id} 已删除",
        request=request
    )


@router.post("/prompts/{prompt_id}/render", response_model=BaseResponse[Dict[str, Any]])
async def render_prompt(
    prompt_id: str,
    variables: Dict[str, Any],
    request: Request
) -> BaseResponse[Dict[str, Any]]:
    """渲染 Prompt（替换变量）"""
    prompt = prompt_store.get_prompt(prompt_id)
    if not prompt:
        return not_found_response(
            resource=f"Prompt {prompt_id}",
            request=request
        )
    
    try:
        rendered = prompt.render(**variables)
        return success_response(
            data={
                "prompt_id": prompt_id,
                "rendered_content": rendered,
                "variables_used": variables
            },
            message="Prompt渲染成功",
            request=request
        )
    except Exception as e:
        logger.error(f"渲染 Prompt 失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"渲染 Prompt 失败: {str(e)}",
            request=request
        )


@router.get("/prompts/{prompt_id}/usage", response_model=BaseResponse[List[PromptUsage]])
async def get_prompt_usage(
    prompt_id: str,
    request: Request,
    limit: int = 100
) -> BaseResponse[List[PromptUsage]]:
    """获取 Prompt 使用历史"""
    usage_history = prompt_store.get_usage_history(prompt_id=prompt_id, limit=limit)
    return success_response(
        data=usage_history,
        message=f"获取到 {len(usage_history)} 条使用记录",
        request=request
    )


@router.get("/prompts/search/{keyword}", response_model=BaseResponse[List[PromptTemplate]])
async def search_prompts(keyword: str, request: Request) -> BaseResponse[List[PromptTemplate]]:
    """搜索 Prompt"""
    prompts = prompt_store.search_prompts(keyword)
    return success_response(
        data=prompts,
        message=f"搜索到 {len(prompts)} 个Prompt",
        request=request
    )

