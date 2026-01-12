# Agent 使用指南

## Agent 架构说明

系统现在支持两种 Agent 使用方式：

### 1. BaseAgent（独立 Agent）

`BaseAgent` 是一个完全独立的 Agent 类，**不依赖工作流引擎或知识库**，可以单独使用。

**特点**：
- ✅ 完全独立，不依赖其他组件
- ✅ 可以只使用自定义工具
- ✅ 可以自定义 Prompt
- ✅ 轻量级，适合简单场景

**使用场景**：
- 只需要基础工具（API、文件、数据处理等）
- 不需要工作流功能
- 不需要知识库功能
- 想要完全控制 Agent 行为

### 2. WorkflowAgent（工作流 Agent）

`WorkflowAgent` 继承自 `BaseAgent`，添加了工作流和知识库支持。

**特点**：
- ✅ 继承 BaseAgent 的所有功能
- ✅ 可选的工作流支持（如果提供 workflow_engine）
- ✅ 可选的知识库支持（如果提供 knowledge_store）
- ✅ 向后兼容原有代码

**使用场景**：
- 需要工作流功能
- 需要知识库功能
- 需要完整的系统功能

## 使用示例

### 示例1: 独立使用 BaseAgent

```python
from langchain.tools import Tool
from app.agents.base_agent import BaseAgent

# 定义自定义工具
def get_weather(city: str) -> str:
    return f"{city} 的天气：晴天，25°C"

weather_tool = Tool(
    name="get_weather",
    description="获取天气信息。参数: city (城市名称)",
    func=get_weather
)

# 创建独立的 Agent（不依赖工作流或知识库）
agent = BaseAgent(
    tools=[weather_tool],
    prompt_content="你是一个天气助手。"
)

# 使用 Agent
import asyncio
async def test():
    response = await agent.process_message("北京今天天气怎么样？")
    print(response.message)

asyncio.run(test())
```

### 示例2: WorkflowAgent 不使用工作流

```python
from app.agents.workflow_agent import WorkflowAgent

# 创建 Agent，但不提供 workflow_engine（相当于独立 Agent）
agent = WorkflowAgent(
    workflow_engine=None,  # 不提供工作流引擎
    knowledge_store=None,   # 不提供知识库
    tools=[custom_tool],    # 只使用自定义工具
    prompt_content="你是一个助手。"
)

# 使用方式与 BaseAgent 相同
response = await agent.process_message("你好")
```

### 示例3: WorkflowAgent 完整功能

```python
from app.agents.workflow_agent import WorkflowAgent
from app.workflows.engine import WorkflowEngine
from app.storage.knowledge_store import KnowledgeStore

# 创建完整功能的 Agent
workflow_engine = WorkflowEngine(...)
knowledge_store = KnowledgeStore()

agent = WorkflowAgent(
    workflow_engine=workflow_engine,  # 提供工作流引擎
    knowledge_store=knowledge_store,   # 提供知识库
    tools=[custom_tool]                # 还可以添加自定义工具
)

# Agent 现在可以使用工作流和知识库功能
response = await agent.process_message("帮我执行数据分析工作流")
```

## API 使用

### 独立 Agent API（需要新增）

如果需要通过 API 使用独立 Agent，可以创建新的 API 端点：

```python
# app/api/agent.py
from app.agents.base_agent import BaseAgent
from langchain.tools import Tool

@router.post("/agent/chat")
async def agent_chat(request: ChatRequest):
    # 创建独立 Agent
    agent = BaseAgent(
        tools=[...],  # 你的工具
        prompt_content="..."
    )
    
    response = await agent.process_message(request.message)
    return response
```

## 总结

- ✅ **BaseAgent**: 完全独立，不依赖工作流或知识库
- ✅ **WorkflowAgent**: 可选的工作流和知识库支持
- ✅ **灵活组合**: 可以根据需求选择使用哪种 Agent
- ✅ **向后兼容**: 现有代码无需修改

现在系统支持：
1. **独立 Agent** - 只使用工具，不依赖其他组件
2. **工作流 Agent** - 可选的工作流和知识库支持
3. **完全控制** - 可以自定义工具和 Prompt

