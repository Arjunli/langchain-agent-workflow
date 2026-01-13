"""基础 Agent 类"""
from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from app.models.agent import AgentResponse
from app.storage.prompt_store import PromptStore
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """基础 Agent 类，可以独立使用，不依赖工作流或知识库"""
    
    def __init__(
        self,
        tools: Optional[List[Tool]] = None,
        prompt_content: Optional[str] = None,
        prompt_store: Optional[PromptStore] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        初始化基础 Agent
        
        Args:
            tools: LangChain 工具列表（可选）
            prompt_content: Prompt 内容（可选，如果不提供则使用默认）
            prompt_store: Prompt 存储（可选）
            llm_model: LLM 模型名称（可选，默认使用配置）
            temperature: LLM 温度（可选，默认使用配置）
        """
        self.tools = tools or []
        self.prompt_store = prompt_store
        self.prompt_content = prompt_content
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=llm_model or settings.openai_model,
            temperature=temperature if temperature is not None else settings.openai_temperature,
            api_key=settings.openai_api_key
        )
        
        self.agent_executor: Optional[AgentExecutor] = None
        self._default_prompt_id: Optional[str] = None
        self._initialize_agent()
    
    def _initialize_agent(self, prompt_id: Optional[str] = None):
        """初始化 Agent"""
        # 获取 Prompt 内容
        prompt_content = self._get_prompt_content(prompt_id)
        
        # 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_content),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建 Agent
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        # 创建 AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_prompt_content(self, prompt_id: Optional[str] = None) -> str:
        """获取 Prompt 内容"""
        # 如果指定了 prompt_id，使用指定的 Prompt
        if prompt_id and self.prompt_store:
            prompt = self.prompt_store.get_prompt(prompt_id)
            if prompt:
                # 渲染 Prompt（使用默认变量）
                return prompt.render()
        
        # 尝试获取默认 Prompt
        if self.prompt_store:
            default_prompt = self.prompt_store.get_default_prompt()
            if default_prompt:
                return default_prompt.render()
        
        # 使用提供的 prompt_content
        if self.prompt_content:
            return self.prompt_content
        
        # 使用默认 Prompt
        return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """获取默认 Prompt"""
        tool_descriptions = []
        if self.tools:
            tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in self.tools]
        
        tools_section = "\n".join(tool_descriptions) if tool_descriptions else "暂无可用工具"
        
        return f"""你是一个智能助手。你的任务是理解用户的意图，并使用可用工具来帮助用户完成任务。

可用工具：
{tools_section}

工作流程：
1. 理解用户的意图
2. 选择合适的工具来完成任务
3. 执行工具并获取结果
4. 向用户报告结果

请用中文回复用户。如果用户的问题无法通过可用工具解决，请礼貌地告知用户。"""
    
    def add_tool(self, tool: Tool):
        """添加工具"""
        self.tools.append(tool)
        # 重新初始化 Agent 以包含新工具
        self._initialize_agent()
    
    def remove_tool(self, tool_name: str):
        """移除工具"""
        self.tools = [t for t in self.tools if t.name != tool_name]
        # 重新初始化 Agent
        self._initialize_agent()
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[str] = None,
        stream: bool = False
    ) -> AgentResponse:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            context: 上下文信息
            prompt_id: Prompt ID
            stream: 是否使用流式响应
        
        Returns:
            Agent响应
        """
        try:
            # 如果指定了不同的 prompt_id，重新初始化 Agent
            if prompt_id and prompt_id != self._default_prompt_id:
                self._default_prompt_id = prompt_id
                self._initialize_agent(prompt_id=prompt_id)
            
            # 记录 Prompt 使用
            if prompt_id and self.prompt_store:
                from app.models.prompt import PromptUsage
                import uuid
                usage = PromptUsage(
                    id=str(uuid.uuid4()),
                    prompt_id=prompt_id,
                    conversation_id=context.get("conversation_id") if context else None,
                    variables_used={}
                )
                self.prompt_store.record_usage(usage)
            
            # 调用 Agent（非流式）
            result = await self.agent_executor.ainvoke({
                "input": message
            })
            
            return AgentResponse(
                message=result.get("output", ""),
                workflow_triggered=False,
                tool_calls=result.get("intermediate_steps", []),
                metadata={"agent_output": result, "prompt_id": prompt_id}
            )
        
        except Exception as e:
            logger.error(f"Agent 处理消息失败: {e}", exc_info=True)
            return AgentResponse(
                message=f"处理消息时出错: {str(e)}",
                workflow_triggered=False,
                metadata={"error": str(e)}
            )
    
    async def process_message_stream(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        prompt_id: Optional[str] = None,
        response_id: Optional[str] = None
    ) -> AgentResponse:
        """
        处理用户消息（流式响应，带缓冲区保护）
        
        Args:
            message: 用户消息
            context: 上下文信息
            prompt_id: Prompt ID
            response_id: 响应ID（用于追踪）
        
        Returns:
            Agent响应（包含完整或部分内容）
        """
        import uuid
        from app.utils.llm_response import get_response_handler
        
        response_id = response_id or str(uuid.uuid4())
        conversation_id = context.get("conversation_id") if context else None
        response_handler = get_response_handler()
        
        try:
            # 如果指定了不同的 prompt_id，重新初始化 Agent
            if prompt_id and prompt_id != self._default_prompt_id:
                self._default_prompt_id = prompt_id
                self._initialize_agent(prompt_id=prompt_id)
            
            # 记录 Prompt 使用
            if prompt_id and self.prompt_store:
                from app.models.prompt import PromptUsage
                usage = PromptUsage(
                    id=str(uuid.uuid4()),
                    prompt_id=prompt_id,
                    conversation_id=conversation_id,
                    variables_used={}
                )
                self.prompt_store.record_usage(usage)
            
            # 使用流式调用并收集结果
            buffer = response_handler.create_buffer(response_id, conversation_id)
            full_output = ""
            
            try:
                async for chunk in self.agent_executor.astream({
                    "input": message
                }):
                    # 提取输出内容
                    chunk_text = ""
                    if isinstance(chunk, dict):
                        # AgentExecutor返回的chunk格式
                        if "output" in chunk:
                            chunk_text = str(chunk["output"])
                        elif "agent" in chunk and "return_values" in chunk["agent"]:
                            chunk_text = str(chunk["agent"]["return_values"].get("output", ""))
                        elif "tool" in chunk:
                            # 工具调用，可以记录但不作为输出
                            continue
                    
                    if chunk_text:
                        buffer.append(chunk_text)
                        full_output += chunk_text
                
                buffer.mark_complete()
                
            except Exception as stream_error:
                logger.warning(f"流式响应中断: {response_id}, 错误: {stream_error}")
                buffer.mark_error(str(stream_error))
                # 继续使用已收集的内容
            
            # 返回响应（完整或部分）
            return AgentResponse(
                message=buffer.get_content() or full_output,
                workflow_triggered=False,
                tool_calls=[],
                metadata={
                    "response_id": response_id,
                    "prompt_id": prompt_id,
                    "streamed": True,
                    "complete": buffer.complete,
                    "partial": not buffer.complete and bool(buffer.get_content())
                }
            )
            
        except Exception as e:
            logger.error(f"Agent 流式处理消息失败: {e}", exc_info=True)
            # 尝试返回部分响应
            buffer = response_handler.get_buffer(response_id)
            if buffer and buffer.get_partial_content():
                logger.info(f"返回部分响应: {response_id}")
                return AgentResponse(
                    message=buffer.get_partial_content(),
                    workflow_triggered=False,
                    tool_calls=[],
                    metadata={
                        "response_id": response_id,
                        "error": str(e),
                        "partial": True
                    }
                )
            
            return AgentResponse(
                message=f"处理消息时出错: {str(e)}",
                workflow_triggered=False,
                metadata={"error": str(e), "response_id": response_id}
            )

