"""独立 Agent 使用示例"""
from langchain.tools import Tool
from app.agents.base_agent import BaseAgent


# 示例1: 创建一个完全独立的 Agent，只使用基础工具
def example_standalone_agent():
    """示例：独立 Agent，不依赖工作流或知识库"""
    
    # 定义一些简单的工具
    def get_weather(city: str) -> str:
        """获取天气信息"""
        return f"{city} 的天气：晴天，25°C"
    
    def calculate(expression: str) -> str:
        """计算数学表达式"""
        try:
            result = eval(expression)
            return f"计算结果：{result}"
        except:
            return "计算错误"
    
    # 创建工具
    weather_tool = Tool(
        name="get_weather",
        description="获取指定城市的天气信息。参数: city (城市名称)",
        func=get_weather
    )
    
    calc_tool = Tool(
        name="calculate",
        description="计算数学表达式。参数: expression (数学表达式，如 '2+2')",
        func=calculate
    )
    
    # 创建独立的 Agent（不依赖工作流或知识库）
    agent = BaseAgent(
        tools=[weather_tool, calc_tool],
        prompt_content="你是一个有用的助手。你可以帮助用户查询天气和进行数学计算。"
    )
    
    # 使用 Agent
    import asyncio
    async def test():
        response = await agent.process_message("北京今天天气怎么样？")
        print(response.message)
        
        response = await agent.process_message("帮我计算 123 + 456")
        print(response.message)
    
    asyncio.run(test())


# 示例2: 使用自定义 Prompt
def example_custom_prompt_agent():
    """示例：使用自定义 Prompt 的独立 Agent"""
    
    # 创建工具
    def search_web(query: str) -> str:
        """搜索网络"""
        return f"搜索结果：关于 '{query}' 的信息..."
    
    search_tool = Tool(
        name="search_web",
        description="搜索网络信息。参数: query (搜索关键词)",
        func=search_web
    )
    
    # 使用自定义 Prompt
    custom_prompt = """你是一个专业的搜索助手。你的任务是：
1. 理解用户的搜索需求
2. 使用 search_web 工具搜索相关信息
3. 整理搜索结果并回复用户

请用中文回复。"""
    
    agent = BaseAgent(
        tools=[search_tool],
        prompt_content=custom_prompt
    )
    
    # 使用 Agent
    import asyncio
    async def test():
        response = await agent.process_message("搜索一下 Python 的最新特性")
        print(response.message)
    
    asyncio.run(test())


# 示例3: 动态添加工具
def example_dynamic_tools():
    """示例：动态添加工具"""
    
    agent = BaseAgent(
        tools=[],
        prompt_content="你是一个助手。"
    )
    
    # 动态添加工具
    def translate(text: str, target_lang: str = "en") -> str:
        """翻译文本"""
        return f"翻译结果：{text} -> {target_lang}"
    
    translate_tool = Tool(
        name="translate",
        description="翻译文本。参数: text (要翻译的文本), target_lang (目标语言，默认'en')",
        func=translate
    )
    
    agent.add_tool(translate_tool)
    
    # 使用 Agent
    import asyncio
    async def test():
        response = await agent.process_message("把 '你好' 翻译成英文")
        print(response.message)
    
    asyncio.run(test())


if __name__ == "__main__":
    print("示例1: 独立 Agent")
    example_standalone_agent()
    
    print("\n示例2: 自定义 Prompt")
    example_custom_prompt_agent()
    
    print("\n示例3: 动态添加工具")
    example_dynamic_tools()

