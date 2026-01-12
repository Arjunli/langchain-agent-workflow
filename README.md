# LangChain Agent 工作流系统

一个功能强大的基于 LangChain 的智能 Agent 系统，支持通过自然语言聊天调用复杂工作流、检索知识库、管理 Prompt 模板。系统集成了工作流引擎、向量数据库、RAG 能力，为构建智能自动化应用提供了完整的解决方案。

## 核心价值

- 🚀 **开箱即用**: 快速搭建智能 Agent 系统，无需从零开始
- 🔧 **灵活扩展**: 模块化设计，易于添加自定义工具和工作流
- 🧠 **智能理解**: 基于 LLM 的意图理解，自然语言交互
- 📦 **功能完整**: 工作流、知识库、Prompt 管理一应俱全

## 功能特性

### 🤖 智能 Agent
- 基于 LangChain 的 Agent 框架，支持工具调用和链式推理
- 自动理解用户意图，智能选择和执行工作流
- 支持多轮对话，维护上下文信息
- 可配置的 Agent 行为（通过 Prompt 管理）

### 🔄 工作流引擎
- **多种节点类型**: START、END、TASK、CONDITION、LOOP、PARALLEL
- **复杂流程支持**: 条件分支、循环、并行执行
- **变量系统**: 支持变量替换和传递（`${variable}`）
- **状态管理**: 工作流执行状态持久化，支持恢复和重试
- **格式支持**: 支持 YAML 和 JSON 格式定义工作流

### 💬 聊天接口
- **RESTful API**: 标准 HTTP 接口，易于集成
- **WebSocket 支持**: 实时双向通信
- **流式响应**: 支持 Server-Sent Events（SSE）
- **对话管理**: 自动维护对话历史和上下文

### 🛠️ 工具集成
- **API 调用工具**: 支持 GET/POST/PUT/DELETE，同步/异步执行
- **文件操作工具**: 读取、写入、删除文件，目录列表
- **数据处理工具**: JSON 解析、数据过滤、转换
- **代码执行工具**: Python 代码执行（可选，需沙箱环境）
- **易于扩展**: 简单的工具注册机制，快速添加新工具

### 📚 知识库系统
- **向量数据库**: 集成 FAISS 和 Chroma，支持大规模文档存储
- **RAG 能力**: 检索增强生成，结合知识库内容回答问题
- **文档管理**: 支持文档上传、分块、嵌入
- **相似度搜索**: 基于语义的文档检索
- **自动集成**: Agent 自动调用知识库工具检索相关信息

### 📝 Prompt 管理
- **模板系统**: 支持变量替换的 Prompt 模板
- **Prompt 库**: 创建、编辑、删除、搜索 Prompt
- **默认 Prompt**: 支持设置默认 Prompt，自动应用
- **使用统计**: 记录 Prompt 使用次数和历史
- **动态切换**: 运行时切换不同的 Prompt，改变 Agent 行为

### 📊 状态管理
- **工作流状态**: 持久化工作流执行状态
- **对话历史**: 保存对话记录，支持上下文恢复
- **使用记录**: 跟踪 Prompt 和工具的使用情况

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层                            │
│  RESTful API / WebSocket / 流式响应                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Agent 层                                │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ WorkflowAgent│  │  ChatAgent   │                    │
│  │  - 意图理解   │  │  - 对话管理   │                    │
│  │  - 工具调用   │  │  - 上下文维护 │                    │
│  └──────────────┘  └──────────────┘                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              核心功能层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ 工作流引擎    │  │ 知识库系统   │  │ Prompt管理   │   │
│  │ - 执行引擎    │  │ - 向量存储   │  │ - 模板管理   │   │
│  │ - 状态机      │  │ - RAG检索    │  │ - 变量替换   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 工具层                                    │
│  API调用 / 文件操作 / 数据处理 / 代码执行                 │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
langchain-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   │
│   ├── models/                 # 数据模型
│   │   ├── workflow.py        # 工作流模型
│   │   ├── message.py          # 消息模型
│   │   ├── agent.py            # Agent 状态模型
│   │   ├── knowledge.py        # 知识库模型
│   │   └── prompt.py           # Prompt 模型
│   │
│   ├── agents/                 # Agent 实现
│   │   ├── workflow_agent.py  # 工作流 Agent
│   │   └── chat_agent.py       # 聊天 Agent
│   │
│   ├── workflows/              # 工作流引擎
│   │   ├── engine.py           # 工作流引擎
│   │   ├── registry.py        # 工作流注册表
│   │   └── executor.py         # 工作流执行器
│   │
│   ├── tools/                  # LangChain 工具
│   │   ├── registry.py        # 工具注册表
│   │   ├── api_tool.py         # API 调用工具
│   │   ├── file_tool.py        # 文件操作工具
│   │   ├── data_tool.py        # 数据处理工具
│   │   ├── code_tool.py        # 代码执行工具
│   │   └── knowledge_tool.py   # 知识库检索工具
│   │
│   ├── api/                    # API 路由
│   │   ├── chat.py             # 聊天接口
│   │   ├── workflow.py         # 工作流管理接口
│   │   ├── knowledge.py         # 知识库管理接口
│   │   ├── prompt.py            # Prompt 管理接口
│   │   └── websocket.py         # WebSocket 支持
│   │
│   └── storage/                # 存储层
│       ├── workflow_store.py   # 工作流存储
│       ├── conversation_store.py # 对话存储
│       ├── knowledge_store.py   # 知识库存储
│       └── prompt_store.py     # Prompt 存储
│
├── examples/                   # 示例文件
│   ├── workflow_example.yaml   # 工作流示例（YAML）
│   ├── workflow_example.json   # 工作流示例（JSON）
│   ├── knowledge_base_example.md # 知识库使用示例
│   ├── prompt_example.json     # Prompt 示例
│   └── prompt_example.md       # Prompt 使用示例
│
├── tests/                      # 测试
│   └── test_workflow.py        # 工作流测试
│
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略文件
├── README.md                   # 项目说明（本文件）
├── USAGE.md                    # 详细使用指南
└── run.py                      # 启动脚本
```

## 技术栈

- **后端框架**: FastAPI
- **Agent 框架**: LangChain
- **LLM**: OpenAI GPT（可配置其他 LLM）
- **向量数据库**: FAISS / Chroma
- **数据验证**: Pydantic
- **异步支持**: asyncio / aiohttp
- **存储**: 文件系统（可扩展为数据库）

## 快速开始

### 前置要求

- Python 3.8+
- OpenAI API Key（或其他兼容的 LLM API Key）

### 1. 克隆项目

```bash
git clone <repository-url>
cd langchain-agent
```

### 2. 安装依赖

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 py（Windows）
py -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API 配置（必需）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# 数据库配置（可选）
DATABASE_URL=sqlite:///./workflows.db

# 工作流配置
WORKFLOW_TIMEOUT=3600
MAX_RETRIES=3

# 日志配置
LOG_LEVEL=INFO
```

### 4. 运行服务

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: Windows 使用 py
py run.py
```

服务启动后，访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## API 文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用示例

### 1. 聊天接口

**基础聊天**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行数据分析工作流"
  }'
```

**使用自定义 Prompt**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行数据分析工作流",
    "prompt_id": "my_custom_prompt",
    "conversation_id": "conv_123"
  }'
```

**流式响应**:
```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行数据分析工作流",
    "stream": true
  }'
```

### 2. 工作流管理

**创建工作流**:
```bash
# 从 JSON 创建
curl -X POST "http://localhost:8000/api/workflows" \
  -H "Content-Type: application/json" \
  -d @examples/workflow_example.json

# 从 YAML 上传
curl -X POST "http://localhost:8000/api/workflows/upload" \
  -F "file=@examples/workflow_example.yaml"
```

**列出所有工作流**:
```bash
curl "http://localhost:8000/api/workflows"
```

**执行工作流**:
```bash
curl -X POST "http://localhost:8000/api/workflows/{workflow_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "input_data": "test"
    }
  }'
```

**搜索工作流**:
```bash
curl "http://localhost:8000/api/workflows/search/数据分析"
```

### 3. 知识库管理

**创建知识库**:
```bash
curl -X POST "http://localhost:8000/api/knowledge-bases" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_kb",
    "name": "我的知识库",
    "description": "示例知识库",
    "embedding_model": "text-embedding-ada-002",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }'
```

**添加文档**:
```bash
# 方式1: 直接添加文本
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc1",
    "content": "文档内容...",
    "title": "文档标题",
    "knowledge_base_id": "my_kb",
    "metadata": {
      "category": "技术文档"
    }
  }'

# 方式2: 上传文件
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/documents/upload" \
  -F "file=@document.txt" \
  -F "title=文档标题"
```

**搜索文档**:
```bash
curl -X POST "http://localhost:8000/api/knowledge-bases/my_kb/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "搜索关键词",
    "knowledge_base_id": "my_kb",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

**Agent 自动使用知识库**:
```bash
# Agent 会自动调用知识库工具检索相关信息
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "LangChain 是什么？请从知识库中查找相关信息"
  }'
```

### 4. Prompt 管理

**创建 Prompt**:
```bash
curl -X POST "http://localhost:8000/api/prompts" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_prompt",
    "name": "我的 Prompt",
    "description": "自定义 Prompt 模板",
    "content": "你是一个专业的助手。可用工作流：{workflow_list}",
    "prompt_type": "template",
    "variables": ["workflow_list"],
    "category": "workflow",
    "tags": ["custom", "assistant"],
    "is_default": false,
    "is_active": true
  }'
```

**列出所有 Prompt**:
```bash
# 列出所有
curl "http://localhost:8000/api/prompts"

# 按分类筛选
curl "http://localhost:8000/api/prompts?category=workflow"

# 按标签筛选
curl "http://localhost:8000/api/prompts?tags=custom,assistant"
```

**渲染 Prompt（测试变量替换）**:
```bash
curl -X POST "http://localhost:8000/api/prompts/my_prompt/render" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "workflow_list": "工作流1, 工作流2"
    }
  }'
```

**在聊天中使用自定义 Prompt**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行工作流",
    "prompt_id": "my_prompt"
  }'
```

**查看 Prompt 使用历史**:
```bash
curl "http://localhost:8000/api/prompts/my_prompt/usage?limit=50"
```

## 工作流示例

### 简单工作流（YAML）

```yaml
id: simple_workflow
name: 简单工作流
description: 一个简单的 API 调用工作流

nodes:
  - id: start
    name: 开始
    type: start
  
  - id: api_call
    name: 调用API
    type: task
    tool_name: api_call
    tool_params:
      url: "https://api.example.com/data"
      method: "GET"
  
  - id: end
    name: 结束
    type: end

edges:
  - source: start
    target: api_call
  - source: api_call
    target: end
```

### 条件分支工作流

```yaml
id: conditional_workflow
name: 条件分支工作流

nodes:
  - id: start
    type: start
  
  - id: task1
    type: task
    tool_name: api_call
    tool_params:
      url: "https://api.example.com/check"
  
  - id: condition
    type: condition
    condition_expr: "${task1_result.status_code} == 200"
  
  - id: success_task
    type: task
    tool_name: file_operation
    tool_params:
      operation: "write"
      file_path: "./success.log"
  
  - id: fail_task
    type: task
    tool_name: file_operation
    tool_params:
      operation: "write"
      file_path: "./error.log"
  
  - id: end
    type: end

edges:
  - source: start
    target: task1
  - source: task1
    target: condition
  - source: condition
    target: success_task
    condition: "${condition_result} == True"
  - source: condition
    target: fail_task
    condition: "${condition_result} == False"
  - source: success_task
    target: end
  - source: fail_task
    target: end
```

## 常见问题（FAQ）

### Q: 如何添加自定义工具？

A: 继承 `BaseTool` 类，实现 `run` 方法，然后注册到 `tool_registry`：

```python
from app.tools.registry import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="我的自定义工具"
        )
    
    def run(self, **kwargs):
        # 实现工具逻辑
        return {"result": "success"}

# 注册工具
from app.tools import tool_registry
tool_registry.register(MyCustomTool())
```

### Q: 如何切换不同的 LLM？

A: 修改 `.env` 文件中的 `OPENAI_MODEL` 配置，或使用其他 LangChain 兼容的 LLM 提供者。

### Q: 知识库支持哪些文件格式？

A: 目前支持文本文件（.txt, .md 等），文件内容会被读取为文本并分块处理。

### Q: 如何持久化工作流和对话数据？

A: 当前使用文件系统存储，可以修改存储层实现使用数据库（如 PostgreSQL、MongoDB）。

### Q: 工作流执行失败如何处理？

A: 工作流执行器会自动记录错误信息，可以通过 API 查询工作流状态和错误详情。

## 开发计划

- [x] Phase 1: 基础框架搭建
- [x] Phase 2: 工作流引擎
- [x] Phase 3: 工具集成
- [x] Phase 4: LangChain Agent
- [x] Phase 5: 聊天接口
- [x] Phase 6: 知识库系统（RAG）
- [x] Phase 7: Prompt 管理系统
- [ ] Phase 8: 工作流可视化界面
- [ ] Phase 9: 监控和日志系统
- [ ] Phase 10: 性能优化和缓存
- [ ] Phase 11: 多租户支持
- [ ] Phase 12: 权限和认证系统

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 相关资源

- [LangChain 文档](https://python.langchain.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [OpenAI API 文档](https://platform.openai.com/docs)

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

