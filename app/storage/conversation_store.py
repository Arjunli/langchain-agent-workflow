"""对话存储"""
from typing import Optional, List
from app.models.message import Conversation
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationStore:
    """对话存储（文件系统实现）"""
    
    def __init__(self, storage_path: str = "./storage/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, conversation: Conversation) -> None:
        """保存对话"""
        file_path = self.storage_path / f"{conversation.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"对话已保存: {conversation.id}")
    
    def load(self, conversation_id: str) -> Optional[Conversation]:
        """加载对话"""
        file_path = self.storage_path / f"{conversation_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换时间戳
        for msg in data.get('messages', []):
            if 'timestamp' in msg:
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
        
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return Conversation(**data)
    
    def list_all(self) -> List[str]:
        """列出所有对话ID"""
        return [f.stem for f in self.storage_path.glob("*.json")]

