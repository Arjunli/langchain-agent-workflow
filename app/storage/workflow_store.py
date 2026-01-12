"""工作流存储"""
from typing import Optional, List
from app.models.workflow import Workflow
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WorkflowStore:
    """工作流存储（文件系统实现）"""
    
    def __init__(self, storage_path: str = "./storage/workflows"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, workflow: Workflow) -> None:
        """保存工作流"""
        file_path = self.storage_path / f"{workflow.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(workflow.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"工作流已保存: {workflow.id}")
    
    def load(self, workflow_id: str) -> Optional[Workflow]:
        """加载工作流"""
        file_path = self.storage_path / f"{workflow_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Workflow(**data)
    
    def list_all(self) -> List[str]:
        """列出所有工作流ID"""
        return [f.stem for f in self.storage_path.glob("*.json")]
    
    def delete(self, workflow_id: str) -> bool:
        """删除工作流"""
        file_path = self.storage_path / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

