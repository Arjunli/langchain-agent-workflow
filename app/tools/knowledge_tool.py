"""知识库检索工具"""
from typing import Dict, Any, Optional, List
from app.tools.registry import BaseTool
from app.storage.knowledge_store import KnowledgeStore
import logging

logger = logging.getLogger(__name__)


class KnowledgeRetrievalTool(BaseTool):
    """知识库检索工具（RAG）"""
    
    def __init__(self, knowledge_store: KnowledgeStore):
        super().__init__(
            name="knowledge_retrieval",
            description="从知识库中检索相关信息。参数: query (查询文本), knowledge_base_id (知识库ID), top_k (返回结果数量，默认5)"
        )
        self.knowledge_store = knowledge_store
    
    def run(
        self,
        query: str,
        knowledge_base_id: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """执行知识库检索"""
        try:
            # 搜索文档
            results = self.knowledge_store.search_documents(
                kb_id=knowledge_base_id,
                query=query,
                top_k=top_k,
                score_threshold=score_threshold
            )
            
            if not results:
                return {
                    "success": True,
                    "message": "未找到相关文档",
                    "results": [],
                    "count": 0
                }
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document_id": result.document.id,
                    "title": result.document.title,
                    "content": result.document.content,
                    "score": result.score,
                    "metadata": result.document.metadata
                })
            
            # 合并所有相关内容
            combined_content = "\n\n".join([
                f"[文档: {r['title'] or r['document_id']}]\n{r['content']}"
                for r in formatted_results
            ])
            
            return {
                "success": True,
                "message": f"找到 {len(results)} 个相关文档",
                "results": formatted_results,
                "combined_content": combined_content,
                "count": len(results)
            }
        
        except Exception as e:
            logger.error(f"知识库检索失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有知识库"""
        try:
            kbs = self.knowledge_store.list_knowledge_bases()
            return [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "description": kb.description,
                    "document_count": len(kb.document_ids)
                }
                for kb in kbs
            ]
        except Exception as e:
            logger.error(f"列出知识库失败: {e}")
            return []

