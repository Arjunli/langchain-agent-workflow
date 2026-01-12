"""知识库管理 API"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.knowledge import (
    KnowledgeBase, Document, DocumentSearchRequest, DocumentSearchResult
)
from app.storage.knowledge_store import KnowledgeStore
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 初始化知识库存储
knowledge_store = KnowledgeStore()


@router.post("/knowledge-bases", response_model=KnowledgeBase)
async def create_knowledge_base(kb: KnowledgeBase) -> KnowledgeBase:
    """创建知识库"""
    try:
        result = knowledge_store.create_knowledge_base(kb)
        return result
    except Exception as e:
        logger.error(f"创建知识库失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-bases", response_model=List[KnowledgeBase])
async def list_knowledge_bases() -> List[KnowledgeBase]:
    """列出所有知识库"""
    return knowledge_store.list_knowledge_bases()


@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBase)
async def get_knowledge_base(kb_id: str) -> KnowledgeBase:
    """获取知识库"""
    kb = knowledge_store.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    return kb


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str) -> dict:
    """删除知识库"""
    success = knowledge_store.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    return {"success": True, "message": f"知识库 {kb_id} 已删除"}


@router.post("/knowledge-bases/{kb_id}/documents", response_model=Document)
async def add_document(kb_id: str, document: Document) -> Document:
    """添加文档到知识库"""
    try:
        # 确保文档ID存在
        if not document.id:
            document.id = str(uuid.uuid4())
        
        # 确保知识库ID匹配
        document.knowledge_base_id = kb_id
        
        result = knowledge_store.add_document(kb_id, document)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"添加文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-bases/{kb_id}/documents/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = None
) -> Document:
    """上传文档文件到知识库"""
    try:
        # 读取文件内容
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # 创建文档
        document = Document(
            id=str(uuid.uuid4()),
            content=text_content,
            title=title or file.filename,
            knowledge_base_id=kb_id,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type
            }
        )
        
        result = knowledge_store.add_document(kb_id, document)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-bases/{kb_id}/search", response_model=List[DocumentSearchResult])
async def search_documents(
    kb_id: str,
    request: DocumentSearchRequest
) -> List[DocumentSearchResult]:
    """搜索知识库中的文档"""
    try:
        results = knowledge_store.search_documents(
            kb_id=kb_id,
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            metadata_filter=request.metadata_filter
        )
        return results
    except Exception as e:
        logger.error(f"搜索文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge-bases/{kb_id}/documents/{document_id}")
async def delete_document(kb_id: str, document_id: str) -> dict:
    """从知识库中删除文档"""
    success = knowledge_store.delete_document(kb_id, document_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"文档不存在: {document_id} 或知识库不存在: {kb_id}"
        )
    return {"success": True, "message": f"文档 {document_id} 已删除"}

