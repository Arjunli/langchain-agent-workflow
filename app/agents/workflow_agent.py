"""工作流 Agent"""
from typing import Dict, Any, Optional, List

# LangChain 1.2.0 导入
from langchain_core.tools import StructuredTool
from langchain_core.tools import BaseTool as LangChainTool
from app.workflows.engine import WorkflowEngine
from app.storage.knowledge_store import KnowledgeStore
from app.storage.prompt_store import PromptStore
from app.tools.knowledge_tool import KnowledgeRetrievalTool
from app.agents.base_agent import BaseAgent
from app.models.agent import AgentResponse
from app.config import settings
import logging
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowAgent(BaseAgent):
    """工作流 Agent，继承自 BaseAgent，添加工作流和知识库支持"""
    
    def __init__(
        self,
        workflow_engine: Optional[WorkflowEngine] = None,
        knowledge_store: Optional[KnowledgeStore] = None,
        prompt_store: Optional[PromptStore] = None,
        tools: Optional[List[LangChainTool]] = None,
        prompt_content: Optional[str] = None
    ):
        """
        初始化工作流 Agent
        
        Args:
            workflow_engine: 工作流引擎（可选，如果提供则添加工作流工具）
            knowledge_store: 知识库存储（可选，如果提供则添加知识库工具）
            prompt_store: Prompt 存储（可选）
            tools: 额外的工具列表（可选）
            prompt_content: 自定义 Prompt 内容（可选）
        """
        # 构建工具列表
        agent_tools = tools or []
        
        # 如果提供了工作流引擎，添加工作流工具
        if workflow_engine:
            self.workflow_engine = workflow_engine
            workflow_tool = StructuredTool.from_function(
                name="execute_workflow",
                description="执行指定的工作流。参数: workflow_id (工作流ID), variables (可选的工作流变量字典)",
                func=self._execute_workflow_tool
            )
            search_tool = StructuredTool.from_function(
                name="search_workflows",
                description="搜索可用的工作流。参数: keyword (搜索关键词)",
                func=self._search_workflows_tool
            )
            agent_tools.extend([workflow_tool, search_tool])
        else:
            self.workflow_engine = None
        
        # 如果提供了知识库，添加知识库工具
        if knowledge_store:
            self.knowledge_store = knowledge_store
            knowledge_retrieval = KnowledgeRetrievalTool(knowledge_store)
            def search_kb_func(query: str, knowledge_base_id: str, top_k: int = 5) -> str:
                return str(knowledge_retrieval.run(
                    query=query,
                    knowledge_base_id=knowledge_base_id,
                    top_k=top_k
                ))
            
            knowledge_tool = StructuredTool.from_function(
                name="search_knowledge_base",
                description="从知识库中检索相关信息。参数: query (查询文本), knowledge_base_id (知识库ID), top_k (返回结果数量，默认5)",
                func=search_kb_func
            )
            
            def list_kb_func() -> str:
                return str(knowledge_retrieval.list_knowledge_bases())
            
            list_kb_tool = StructuredTool.from_function(
                name="list_knowledge_bases",
                description="列出所有可用的知识库",
                func=list_kb_func
            )
            agent_tools.extend([knowledge_tool, list_kb_tool])
        else:
            self.knowledge_store = None
        
        # 获取 Prompt 内容（如果没有提供，使用默认）
        if not prompt_content:
            prompt_content = self._get_default_workflow_prompt()
        
        # 调用父类初始化
        super().__init__(
            tools=agent_tools,
            prompt_content=prompt_content,
            prompt_store=prompt_store
        )
        
        # 追踪活跃的异步任务
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_metadata: Dict[str, Dict[str, Any]] = {}
    
    def _get_default_workflow_prompt(self) -> str:
        """获取默认工作流 Prompt"""
        workflow_list = self._get_workflow_list()
        knowledge_instructions = self._get_knowledge_instructions()
        
        return f"""你是一个智能助手，可以帮助用户执行工作流和检索知识库信息。

可用工作流：
{workflow_list}

工作流工具：
- search_workflows: 搜索可用的工作流（参数：keyword）
- execute_workflow: 执行指定的工作流（参数：workflow_id, variables）

{knowledge_instructions}

工作流程：
1. 理解用户的意图
2. 如果需要执行工作流，先使用 search_workflows 搜索相关工作流
3. 使用 execute_workflow 执行找到的工作流
4. 如果需要参考知识库，使用知识库工具检索信息
5. 向用户报告结果

请用中文回复用户。如果用户的问题无法通过可用工具解决，请礼貌地告知用户。"""
    
    def _get_knowledge_instructions(self) -> str:
        """获取知识库工具说明"""
        if not self.knowledge_store:
            return ""
        return """
知识库工具：
- list_knowledge_bases: 列出所有可用的知识库
- search_knowledge_base: 从知识库中检索信息（参数：query, knowledge_base_id, top_k）

如果用户的问题需要参考文档或知识库，先使用 list_knowledge_bases 查看可用知识库，然后使用 search_knowledge_base 检索相关信息。
"""
    
    def _get_workflow_list(self) -> str:
        """获取工作流列表描述"""
        if not self.workflow_engine:
            return "暂无可用工作流"
        
        workflows = self.workflow_engine.list_workflows()
        if not workflows:
            return "暂无可用工作流"
        
        descriptions = []
        for wf in workflows:
            desc = f"- {wf.name} (ID: {wf.id})"
            if wf.description:
                desc += f": {wf.description}"
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def _search_workflows_tool(self, keyword: str) -> str:
        """搜索工作流工具"""
        if not self.workflow_engine:
            return "工作流引擎未配置"
        
        workflows = self.workflow_engine.search_workflows(keyword)
        if not workflows:
            return f"未找到包含 '{keyword}' 的工作流"
        
        results = []
        for wf in workflows:
            results.append(f"- {wf.name} (ID: {wf.id}): {wf.description or '无描述'}")
        
        return "\n".join(results)
    
    def _execute_workflow_tool(self, workflow_id: str, variables: Optional[str] = None) -> str:
        """执行工作流工具（同步包装器）"""
        if not self.workflow_engine:
            return "工作流引擎未配置"
        
        try:
            # 解析变量（如果是字符串）
            vars_dict = {}
            if variables:
                try:
                    vars_dict = json.loads(variables) if isinstance(variables, str) else variables
                except:
                    vars_dict = {}
            
            # 检查工作流是否存在
            workflow = self.workflow_engine.get_workflow(workflow_id)
            if not workflow:
                return f"工作流不存在: {workflow_id}"
            
            # 异步执行工作流（在新的事件循环中）
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 如果事件循环正在运行，创建任务但不等待
                task_id = f"workflow_{workflow_id}_{datetime.now().timestamp()}"
                task = asyncio.create_task(
                    self._execute_workflow_with_timeout(workflow_id, vars_dict, task_id)
                )
                # 记录任务
                self._active_tasks[task_id] = task
                self._task_metadata[task_id] = {
                    "workflow_id": workflow_id,
                    "created_at": datetime.now(),
                    "variables": vars_dict
                }
                # 添加完成回调以清理任务
                task.add_done_callback(lambda t: self._cleanup_task(task_id))
                return f"工作流 {workflow_id} 已开始执行（异步）"
            else:
                # 如果事件循环未运行，直接运行
                result = loop.run_until_complete(self.workflow_engine.execute_workflow(workflow_id, vars_dict))
                return f"工作流 {workflow_id} 执行完成，状态: {result.status}"
        
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            return f"执行工作流失败: {str(e)}"
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[str] = None
    ) -> AgentResponse:
        """处理用户消息"""
        # 调用父类方法
        response = await super().process_message(message, context, prompt_id)
        
        # 检查是否触发了工作流
        if self.workflow_engine:
            # 检查工具调用中是否有工作流相关的
            workflow_triggered = any(
                "execute_workflow" in str(step) or "search_workflows" in str(step)
                for step in response.tool_calls
            )
            response.workflow_triggered = workflow_triggered
        
        return response
    
    async def _execute_workflow_with_timeout(
        self,
        workflow_id: str,
        variables: Dict[str, Any],
        task_id: str
    ) -> Any:
        """
        执行工作流（带超时）
        
        Args:
            workflow_id: 工作流ID
            variables: 工作流变量
            task_id: 任务ID
        
        Returns:
            工作流执行结果
        """
        try:
            result = await asyncio.wait_for(
                self.workflow_engine.execute_workflow(workflow_id, variables),
                timeout=settings.task_timeout
            )
            logger.info(f"工作流执行完成: {workflow_id}, 任务ID: {task_id}")
            return result
        except asyncio.TimeoutError:
            logger.error(f"工作流执行超时: {workflow_id}, 任务ID: {task_id}")
            raise
        except Exception as e:
            logger.error(f"工作流执行失败: {workflow_id}, 任务ID: {task_id}, 错误: {e}", exc_info=True)
            raise
    
    def _cleanup_task(self, task_id: str) -> None:
        """
        清理已完成的任务
        
        Args:
            task_id: 任务ID
        """
        if task_id in self._active_tasks:
            del self._active_tasks[task_id]
        if task_id in self._task_metadata:
            del self._task_metadata[task_id]
        logger.debug(f"任务已清理: {task_id}")
    
    def cleanup_tasks(self) -> int:
        """
        清理已完成的任务
        
        Returns:
            清理的任务数量
        """
        completed_tasks = []
        for task_id, task in list(self._active_tasks.items()):
            if task.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            self._cleanup_task(task_id)
        
        if completed_tasks:
            logger.info(f"清理了 {len(completed_tasks)} 个已完成的任务")
        
        return len(completed_tasks)
    
    def get_active_tasks_count(self) -> int:
        """获取活跃任务数量"""
        return len(self._active_tasks)
    
    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            "active_tasks": len(self._active_tasks),
            "task_metadata": {
                task_id: {
                    "workflow_id": meta.get("workflow_id"),
                    "created_at": meta.get("created_at").isoformat() if meta.get("created_at") else None
                }
                for task_id, meta in self._task_metadata.items()
            }
        }

