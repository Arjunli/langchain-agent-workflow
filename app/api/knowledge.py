"""知识库管理 API"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from app.models.knowledge import (
    KnowledgeBase, Document, DocumentSearchRequest, DocumentSearchResult
)
from app.models.response import BaseResponse
from app.utils.response import (
    success_response,
    created_response,
    not_found_response,
    internal_error_response,
    bad_request_response
)
from app.storage.knowledge_store import KnowledgeStore
from typing import List, Optional, Dict, Any
import uuid
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 初始化知识库存储
knowledge_store = KnowledgeStore()


@router.post("/knowledge-bases", response_model=BaseResponse[KnowledgeBase])
async def create_knowledge_base(kb: KnowledgeBase, request: Request) -> BaseResponse[KnowledgeBase]:
    """创建知识库"""
    try:
        result = knowledge_store.create_knowledge_base(kb)
        return created_response(
            data=result,
            message="知识库创建成功",
            request=request
        )
    except Exception as e:
        logger.error(f"创建知识库失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"创建知识库失败: {str(e)}",
            request=request
        )


@router.get("/knowledge-bases", response_model=BaseResponse[List[KnowledgeBase]])
async def list_knowledge_bases(request: Request) -> BaseResponse[List[KnowledgeBase]]:
    """列出所有知识库"""
    knowledge_bases = knowledge_store.list_knowledge_bases()
    return success_response(
        data=knowledge_bases,
        message="获取知识库列表成功",
        request=request
    )


@router.get("/knowledge-bases/{kb_id}", response_model=BaseResponse[KnowledgeBase])
async def get_knowledge_base(kb_id: str, request: Request) -> BaseResponse[KnowledgeBase]:
    """获取知识库"""
    kb = knowledge_store.get_knowledge_base(kb_id)
    if not kb:
        return not_found_response(
            resource=f"知识库 {kb_id}",
            request=request
        )
    return success_response(
        data=kb,
        message="获取知识库成功",
        request=request
    )


@router.delete("/knowledge-bases/{kb_id}", response_model=BaseResponse[Dict[str, Any]])
async def delete_knowledge_base(kb_id: str, request: Request) -> BaseResponse[Dict[str, Any]]:
    """删除知识库"""
    success = knowledge_store.delete_knowledge_base(kb_id)
    if not success:
        return not_found_response(
            resource=f"知识库 {kb_id}",
            request=request
        )
    return success_response(
        data={"kb_id": kb_id},
        message=f"知识库 {kb_id} 已删除",
        request=request
    )


@router.post("/knowledge-bases/{kb_id}/documents", response_model=BaseResponse[Document])
async def add_document(kb_id: str, document: Document, request: Request) -> BaseResponse[Document]:
    """添加文档到知识库"""
    try:
        # 确保文档ID存在
        if not document.id:
            document.id = str(uuid.uuid4())
        
        # 确保知识库ID匹配
        document.knowledge_base_id = kb_id
        
        result = knowledge_store.add_document(kb_id, document)
        return created_response(
            data=result,
            message="文档添加成功",
            request=request
        )
    except ValueError as e:
        return not_found_response(
            resource=str(e),
            request=request
        )
    except Exception as e:
        logger.error(f"添加文档失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"添加文档失败: {str(e)}",
            request=request
        )


@router.post("/knowledge-bases/{kb_id}/documents/upload", response_model=BaseResponse[Document])
async def upload_document(
    kb_id: str,
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = None
) -> BaseResponse[Document]:
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
        return created_response(
            data=result,
            message="文档上传成功",
            request=request
        )
    except ValueError as e:
        return not_found_response(
            resource=str(e),
            request=request
        )
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"上传文档失败: {str(e)}",
            request=request
        )


@router.post("/knowledge-bases/{kb_id}/search", response_model=BaseResponse[List[DocumentSearchResult]])
async def search_documents(
    kb_id: str,
    search_request: DocumentSearchRequest,
    request: Request
) -> BaseResponse[List[DocumentSearchResult]]:
    """搜索知识库中的文档"""
    try:
        results = knowledge_store.search_documents(
            kb_id=kb_id,
            query=search_request.query,
            top_k=search_request.top_k,
            score_threshold=search_request.score_threshold,
            metadata_filter=search_request.metadata_filter
        )
        return success_response(
            data=results,
            message=f"搜索到 {len(results)} 个结果",
            request=request
        )
    except Exception as e:
        logger.error(f"搜索文档失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"搜索文档失败: {str(e)}",
            request=request
        )


@router.delete("/knowledge-bases/{kb_id}/documents/{document_id}", response_model=BaseResponse[Dict[str, Any]])
async def delete_document(kb_id: str, document_id: str, request: Request) -> BaseResponse[Dict[str, Any]]:
    """从知识库中删除文档"""
    success = knowledge_store.delete_document(kb_id, document_id)
    if not success:
        return not_found_response(
            resource=f"文档 {document_id} 或知识库 {kb_id}",
            request=request
        )
    return success_response(
        data={"document_id": document_id, "kb_id": kb_id},
        message=f"文档 {document_id} 已删除",
        request=request
    )

