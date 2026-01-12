"""Prompt 存储"""
from typing import List, Optional, Dict, Any
from app.models.prompt import PromptTemplate, PromptUsage
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptStore:
    """Prompt 存储（文件系统实现）"""
    
    def __init__(self, storage_path: str = "./storage/prompts"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Prompt 元数据文件
        self.prompts_file = self.storage_path / "prompts.json"
        
        # 使用记录目录
        self.usage_path = self.storage_path / "usage"
        self.usage_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._prompts: Dict[str, PromptTemplate] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """加载所有 Prompt"""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for prompt_id, prompt_data in data.items():
                        self._prompts[prompt_id] = PromptTemplate(**prompt_data)
                logger.info(f"已加载 {len(self._prompts)} 个 Prompt")
            except Exception as e:
                logger.error(f"加载 Prompt 失败: {e}")
    
    def _save_prompts(self):
        """保存所有 Prompt"""
        try:
            data = {
                prompt_id: prompt.model_dump() for prompt_id, prompt in self._prompts.items()
            }
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存 Prompt 失败: {e}")
    
    def create_prompt(self, prompt: PromptTemplate) -> PromptTemplate:
        """创建 Prompt"""
        # 如果设置为默认，取消其他默认状态
        if prompt.is_default:
            for p in self._prompts.values():
                if p.is_default and p.id != prompt.id:
                    p.is_default = False
        
        self._prompts[prompt.id] = prompt
        self._save_prompts()
        logger.info(f"Prompt 已创建: {prompt.id}")
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        """获取 Prompt"""
        return self._prompts.get(prompt_id)
    
    def get_default_prompt(self, category: Optional[str] = None) -> Optional[PromptTemplate]:
        """获取默认 Prompt"""
        for prompt in self._prompts.values():
            if prompt.is_default and prompt.is_active:
                if category is None or prompt.category == category:
                    return prompt
        return None
    
    def list_prompts(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        active_only: bool = True
    ) -> List[PromptTemplate]:
        """列出 Prompt"""
        results = []
        for prompt in self._prompts.values():
            if active_only and not prompt.is_active:
                continue
            if category and prompt.category != category:
                continue
            if tags and not any(tag in prompt.tags for tag in tags):
                continue
            results.append(prompt)
        return results
    
    def update_prompt(self, prompt_id: str, **kwargs) -> Optional[PromptTemplate]:
        """更新 Prompt"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        prompt.updated_at = datetime.now()
        
        # 如果设置为默认，取消其他默认状态
        if kwargs.get('is_default') is True:
            for p in self._prompts.values():
                if p.is_default and p.id != prompt_id:
                    p.is_default = False
        
        self._save_prompts()
        logger.info(f"Prompt 已更新: {prompt_id}")
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """删除 Prompt"""
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            self._save_prompts()
            logger.info(f"Prompt 已删除: {prompt_id}")
            return True
        return False
    
    def record_usage(self, usage: PromptUsage) -> None:
        """记录 Prompt 使用"""
        # 更新使用计数
        prompt = self._prompts.get(usage.prompt_id)
        if prompt:
            prompt.usage_count += 1
            self._save_prompts()
        
        # 保存使用记录
        usage_file = self.usage_path / f"{usage.id}.json"
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(usage.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def get_usage_history(self, prompt_id: Optional[str] = None, limit: int = 100) -> List[PromptUsage]:
        """获取使用历史"""
        results = []
        for usage_file in self.usage_path.glob("*.json"):
            try:
                with open(usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    usage = PromptUsage(**data)
                    if prompt_id is None or usage.prompt_id == prompt_id:
                        results.append(usage)
            except Exception as e:
                logger.error(f"加载使用记录失败: {usage_file}, {e}")
        
        # 按时间排序
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]
    
    def search_prompts(self, keyword: str) -> List[PromptTemplate]:
        """搜索 Prompt"""
        keyword_lower = keyword.lower()
        results = []
        for prompt in self._prompts.values():
            if (keyword_lower in prompt.name.lower() or
                (prompt.description and keyword_lower in prompt.description.lower()) or
                keyword_lower in prompt.content.lower()):
                results.append(prompt)
        return results

