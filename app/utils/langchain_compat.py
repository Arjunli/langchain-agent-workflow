"""LangChain 1.2.0 兼容层"""
from typing import List, Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool as Tool
# LLM 导入将在运行时动态加载
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import Runnable
import asyncio
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentExecutor:
    """AgentExecutor 兼容类，使用 LangChain 1.2.0 的新 API"""
    
    def __init__(
        self,
        agent: Any,
        tools: List[Tool],
        verbose: bool = False,
        handle_parsing_errors: bool = True,
        max_iterations: int = 15
    ):
        self.agent = agent
        self.tools = tools
        self.verbose = verbose
        self.handle_parsing_errors = handle_parsing_errors
        self.max_iterations = max_iterations
        self.tool_map = {tool.name: tool for tool in tools}
    
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """同步调用"""
        return asyncio.run(self.ainvoke(inputs))
    
    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """异步调用"""
        user_input = inputs.get("input", "")
        intermediate_steps = []
        agent_scratchpad = []
        
        for iteration in range(self.max_iterations):
            try:
                # 构建 agent 输入
                agent_input = {
                    "input": user_input,
                    "agent_scratchpad": agent_scratchpad
                }
                
                # 调用 agent
                response = await self.agent.ainvoke(agent_input)
                
                # 获取消息列表
                response_messages = response.get("messages", [])
                if not response_messages:
                    # 如果没有消息，尝试直接获取输出
                    output = response.get("output", str(response))
                    return {
                        "output": output,
                        "intermediate_steps": intermediate_steps
                    }
                
                last_message = response_messages[-1]
                
                # 检查是否有工具调用
                tool_calls = None
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    tool_calls = last_message.tool_calls
                elif hasattr(last_message, "additional_kwargs") and "tool_calls" in last_message.additional_kwargs:
                    tool_calls = last_message.additional_kwargs["tool_calls"]
                
                # 如果没有工具调用，返回结果
                if not tool_calls:
                    content = last_message.content if hasattr(last_message, "content") else str(last_message)
                    return {
                        "output": content,
                        "intermediate_steps": intermediate_steps
                    }
                
                # 执行工具调用
                for tool_call in tool_calls:
                    # 解析工具调用
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                        tool_args = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})
                    else:
                        # 如果是对象
                        tool_name = getattr(tool_call, "name", None) or getattr(tool_call, "function", {}).get("name", "")
                        tool_args = getattr(tool_call, "args", {}) or getattr(tool_call, "function", {}).get("arguments", {})
                    
                    if tool_name in self.tool_map:
                        tool = self.tool_map[tool_name]
                        try:
                            if isinstance(tool_args, str):
                                import json
                                tool_args = json.loads(tool_args)
                            
                            # 执行工具
                            if hasattr(tool, "ainvoke"):
                                tool_result = await tool.ainvoke(tool_args)
                            elif asyncio.iscoroutinefunction(tool.invoke):
                                tool_result = await tool.invoke(tool_args)
                            else:
                                tool_result = tool.invoke(tool_args)
                            
                            intermediate_steps.append((tool_name, tool_result))
                            
                            # 添加工具消息到 agent_scratchpad（格式化为字符串）
                            agent_scratchpad.append(f"{tool_name}: {tool_result}")
                        except Exception as e:
                            logger.error(f"工具调用失败 {tool_name}: {e}", exc_info=True)
                            error_msg = f"错误: {str(e)}"
                            intermediate_steps.append((tool_name, error_msg))
                            agent_scratchpad.append(f"{tool_name}: {error_msg}")
                    else:
                        logger.warning(f"未知工具: {tool_name}")
                        agent_scratchpad.append(f"{tool_name}: 未知工具")
                
            except Exception as e:
                if self.handle_parsing_errors:
                    logger.warning(f"解析错误: {e}", exc_info=True)
                    return {
                        "output": f"处理时出错: {str(e)}",
                        "intermediate_steps": intermediate_steps
                    }
                else:
                    raise
        
        return {
            "output": "达到最大迭代次数",
            "intermediate_steps": intermediate_steps
        }
    
    async def astream(self, inputs: Dict[str, Any]):
        """流式调用"""
        # 简化实现：先获取完整结果，然后流式返回
        result = await self.ainvoke(inputs)
        yield {"output": result["output"]}


def create_openai_tools_agent(
    llm: Any,  # 支持任何 ChatModel，不仅仅是 ChatOpenAI
    tools: List[Tool],
    prompt: ChatPromptTemplate
) -> Any:
    """创建 OpenAI 工具 Agent（兼容函数）"""
    
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 创建 agent chain
    class AgentChain:
        def __init__(self, llm_with_tools, prompt):
            self.llm_with_tools = llm_with_tools
            self.prompt = prompt
        
        def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            # 格式化 prompt
            formatted_messages = self.prompt.format_messages(**inputs)
            # 调用 LLM
            response = self.llm_with_tools.invoke(formatted_messages)
            return {"messages": formatted_messages + [response]}
        
        async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            # 格式化 prompt
            formatted_messages = self.prompt.format_messages(**inputs)
            # 调用 LLM
            response = await self.llm_with_tools.ainvoke(formatted_messages)
            return {"messages": formatted_messages + [response]}
        
        async def astream(self, inputs: Dict[str, Any]):
            formatted_messages = self.prompt.format_messages(**inputs)
            async for chunk in self.llm_with_tools.astream(formatted_messages):
                yield {"messages": [chunk]}
    
    return AgentChain(llm_with_tools, prompt)


