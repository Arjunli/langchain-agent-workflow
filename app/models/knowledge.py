"""知识库模型"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 向量相关（可选）
    embedding: Optional[List[float]] = Field(None, description="文档向量嵌入")
    chunk_index: Optional[int] = Field(None, description="文档块索引（如果文档被分块）")


class KnowledgeBase(BaseModel):
    """知识库模型"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    
    # 配置
    embedding_model: str = Field(default="text-embedding-ada-002", description="嵌入模型")
    chunk_size: int = Field(default=1000, description="文档分块大小")
    chunk_overlap: int = Field(default=200, description="文档分块重叠大小")
    
    # 文档列表
    document_ids: List[str] = Field(default_factory=list, description="文档ID列表")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class DocumentSearchRequest(BaseModel):
    """文档搜索请求"""
    query: str = Field(..., description="搜索查询")
    knowledge_base_id: str = Field(..., description="知识库ID")
    top_k: int = Field(default=5, description="返回前K个结果")
    score_threshold: Optional[float] = Field(None, description="相似度阈值")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")


class DocumentSearchResult(BaseModel):
    """文档搜索结果"""
    document: Document = Field(..., description="文档")
    score: float = Field(..., description="相似度分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

