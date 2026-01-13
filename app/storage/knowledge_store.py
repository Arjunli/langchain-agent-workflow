"""知识库存储"""
from typing import List, Optional, Dict, Any
from app.models.knowledge import Document, KnowledgeBase, DocumentSearchResult
from app.utils.cache import LRUCache
from app.config import settings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma, FAISS
from langchain.schema import Document as LangChainDocument
from datetime import datetime
import os
import shutil
from pathlib import Path
import json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeStore:
    """知识库存储（使用向量数据库）"""
    
    def __init__(self, storage_path: str = "./storage/knowledge", use_faiss: bool = True):
        """
        初始化知识库存储
        
        Args:
            storage_path: 存储路径
            use_faiss: 是否使用 FAISS（True）或 Chroma（False）
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.use_faiss = use_faiss
        
        # 知识库元数据存储路径
        self.kb_metadata_path = self.storage_path / "knowledge_bases.json"
        
        # 加载知识库元数据
        self._knowledge_bases: Dict[str, KnowledgeBase] = {}
        self._load_knowledge_bases()
        
        # 初始化嵌入模型
        try:
            from app.config import settings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=settings.openai_api_key
            )
        except Exception as e:
            logger.warning(f"无法初始化嵌入模型: {e}，将使用默认配置")
            self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # 向量存储字典（使用LRU缓存限制内存）
        self._vector_stores = LRUCache(max_size=settings.max_vector_stores)
    
    def _load_knowledge_bases(self):
        """加载知识库元数据"""
        if self.kb_metadata_path.exists():
            try:
                with open(self.kb_metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for kb_id, kb_data in data.items():
                        self._knowledge_bases[kb_id] = KnowledgeBase(**kb_data)
            except Exception as e:
                logger.error(f"加载知识库元数据失败: {e}")
    
    def _save_knowledge_bases(self):
        """保存知识库元数据"""
        try:
            data = {
                kb_id: kb.model_dump() for kb_id, kb in self._knowledge_bases.items()
            }
            with open(self.kb_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存知识库元数据失败: {e}")
    
    def create_knowledge_base(self, kb: KnowledgeBase) -> KnowledgeBase:
        """创建知识库"""
        self._knowledge_bases[kb.id] = kb
        self._save_knowledge_bases()
        logger.info(f"知识库已创建: {kb.id}")
        return kb
    
    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self._knowledge_bases.get(kb_id)
    
    def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """列出所有知识库"""
        return list(self._knowledge_bases.values())
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        if kb_id in self._knowledge_bases:
            # 删除向量存储
            if kb_id in self._vector_stores:
                del self._vector_stores[kb_id]
            
            # 删除向量存储文件
            vector_path = self.storage_path / f"vectors_{kb_id}"
            if vector_path.exists():
                shutil.rmtree(vector_path)
            
            # 删除元数据
            del self._knowledge_bases[kb_id]
            self._save_knowledge_bases()
            logger.info(f"知识库已删除: {kb_id}")
            return True
        return False
    
    def _get_vector_store(self, kb_id: str) -> Optional[Any]:
        """获取向量存储"""
        vector_store = self._vector_stores.get(kb_id)
        if vector_store is None:
            kb = self.get_knowledge_base(kb_id)
            if not kb:
                return None
            
            vector_path = self.storage_path / f"vectors_{kb_id}"
            
            if self.use_faiss:
                # 使用 FAISS
                if vector_path.exists():
                    try:
                        vector_store = FAISS.load_local(
                            str(vector_path),
                            self.embeddings,
                            allow_dangerous_deserialization=True
                        )
                    except Exception as e:
                        logger.error(f"加载 FAISS 向量存储失败: {e}")
                        vector_store = FAISS.from_texts(
                            [""], self.embeddings
                        )
                else:
                    vector_store = FAISS.from_texts(
                        [""], self.embeddings
                    )
            else:
                # 使用 Chroma
                vector_store = Chroma(
                    persist_directory=str(vector_path),
                    embedding_function=self.embeddings
                )
            
            # 存储到LRU缓存
            self._vector_stores.set(kb_id, vector_store)
            return vector_store
        
        return vector_store
    
    def add_document(self, kb_id: str, document: Document) -> Document:
        """添加文档到知识库"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"知识库不存在: {kb_id}")
        
        # 获取或创建向量存储
        vector_store = self._get_vector_store(kb_id)
        if not vector_store:
            vector_store = self._create_vector_store(kb_id)
        
        # 分割文档
        texts = self.text_splitter.split_text(document.content)
        
        # 创建 LangChain 文档
        langchain_docs = []
        for i, text in enumerate(texts):
            metadata = {
                **document.metadata,
                "document_id": document.id,
                "title": document.title or "",
                "chunk_index": i,
                "knowledge_base_id": kb_id
            }
            langchain_docs.append(LangChainDocument(
                page_content=text,
                metadata=metadata
            ))
        
        # 添加到向量存储
        if self.use_faiss:
            vector_store.add_documents(langchain_docs)
            # 保存 FAISS
            vector_path = self.storage_path / f"vectors_{kb_id}"
            vector_store.save_local(str(vector_path))
        else:
            vector_store.add_documents(langchain_docs)
            vector_store.persist()
        
        # 更新缓存（确保LRU顺序正确）
        self._vector_stores.set(kb_id, vector_store)
        
        # 更新知识库
        if document.id not in kb.document_ids:
            kb.document_ids.append(document.id)
        kb.updated_at = datetime.now()
        self._save_knowledge_bases()
        
        logger.info(f"文档已添加到知识库: {document.id} -> {kb_id}")
        return document
    
    def _create_vector_store(self, kb_id: str) -> Any:
        """创建向量存储"""
        vector_path = self.storage_path / f"vectors_{kb_id}"
        
        if self.use_faiss:
            vector_store = FAISS.from_texts([""], self.embeddings)
        else:
            vector_store = Chroma(
                persist_directory=str(vector_path),
                embedding_function=self.embeddings
            )
        
        # 存储到LRU缓存
        self._vector_stores.set(kb_id, vector_store)
        return vector_store
    
    def search_documents(
        self,
        kb_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSearchResult]:
        """搜索文档"""
        vector_store = self._get_vector_store(kb_id)
        if not vector_store:
            return []
        
        # 执行相似度搜索
        if metadata_filter:
            # 带元数据过滤的搜索
            results = vector_store.similarity_search_with_score(
                query,
                k=top_k,
                filter=metadata_filter
            )
        else:
            results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # 转换为搜索结果
        search_results = []
        for doc, score in results:
            # 计算相似度（FAISS 返回的是距离，需要转换为相似度）
            similarity = 1.0 / (1.0 + score) if score > 0 else 1.0
            
            if score_threshold and similarity < score_threshold:
                continue
            
            document = Document(
                id=doc.metadata.get("document_id", ""),
                content=doc.page_content,
                title=doc.metadata.get("title"),
                metadata=doc.metadata,
                knowledge_base_id=kb_id,
                chunk_index=doc.metadata.get("chunk_index")
            )
            
            search_results.append(DocumentSearchResult(
                document=document,
                score=similarity,
                metadata=doc.metadata
            ))
        
        return search_results
    
    def delete_document(self, kb_id: str, document_id: str) -> bool:
        """删除文档"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False
        
        # 从向量存储中删除（注意：某些向量存储可能不支持删除）
        vector_store = self._get_vector_store(kb_id)
        if vector_store:
            # FAISS 和 Chroma 的删除操作较复杂，这里简化处理
            # 实际应用中可能需要重建向量存储
            logger.warning(f"文档删除功能需要重建向量存储: {document_id}")
        
        # 从知识库中移除文档ID
        if document_id in kb.document_ids:
            kb.document_ids.remove(document_id)
            kb.updated_at = datetime.now()
            self._save_knowledge_bases()
            return True
        
        return False

