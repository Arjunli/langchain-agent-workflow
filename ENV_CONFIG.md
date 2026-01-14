# 环境变量配置指南

## 快速开始

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

**PowerShell:**
```powershell
New-Item -Path .env -ItemType File -Force
```

**或者手动创建**：在项目根目录创建名为 `.env` 的文件（注意前面有点）

### 2. 选择 LLM 提供商

#### 使用 OpenAI（需要 API Key）

**在 .env 文件中配置：**
```env
# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
```

## 完整配置示例

### 最小配置

```env
# LLM 配置（必需）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# 消息队列（禁用，不需要 Redis）
QUEUE_ENABLED=false
```

### 完整配置示例

```env
# ============================================
# LLM 配置（必需）
# ============================================

# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# ============================================
# 消息队列配置（可选）
# ============================================

# 禁用消息队列（使用同步模式，不需要 Redis）
QUEUE_ENABLED=false

# 如果启用消息队列，需要配置 Redis
# QUEUE_ENABLED=true
# REDIS_URL=redis://localhost:6379/0

# ============================================
# 日志配置（可选）
# ============================================

LOG_LEVEL=INFO
LOG_DIR=./logs
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true
LOG_JSON_FORMAT=false

# ============================================
# 工作流配置（可选）
# ============================================

WORKFLOW_TIMEOUT=3600
MAX_RETRIES=3

# ============================================
# 缓存配置（可选）
# ============================================

MAX_CONVERSATIONS=1000
CONVERSATION_TTL=3600

# ============================================
# LLM 高级配置（可选）
# ============================================

LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
LLM_STREAM_TIMEOUT=300
LLM_SAVE_PARTIAL=true
```

## 配置项说明

### LLM 配置

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `LLM_PROVIDER` | LLM提供商（目前仅支持 `openai`） | `openai` | 是 |
| `OPENAI_API_KEY` | OpenAI API密钥 | - | 是 |
| `OPENAI_MODEL` | OpenAI模型名称 | `gpt-3.5-turbo` | 否 |
| `OPENAI_TEMPERATURE` | 温度参数（0-1） | `0.7` | 否 |

### 消息队列配置

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `QUEUE_ENABLED` | 是否启用消息队列 | `true` | 否 |
| `REDIS_URL` | Redis连接URL | `redis://localhost:6379/0` | 启用队列时 |

**注意：** 如果 `QUEUE_ENABLED=false`，系统使用同步模式，不需要 Redis。

### 日志配置

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `LOG_LEVEL` | 日志级别：DEBUG, INFO, WARNING, ERROR | `INFO` | 否 |
| `LOG_DIR` | 日志文件目录 | `./logs` | 否 |
| `ENABLE_FILE_LOGGING` | 是否启用文件日志 | `true` | 否 |
| `ENABLE_CONSOLE_LOGGING` | 是否启用控制台日志 | `true` | 否 |
| `LOG_JSON_FORMAT` | 是否使用JSON格式 | `false` | 否 |

### 缓存配置

| 配置项 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `MAX_CONVERSATIONS` | 最大对话缓存数 | `1000` | 否 |
| `CONVERSATION_TTL` | 对话TTL（秒） | `3600` | 否 |

## 常见问题

### 1. OpenAI API Key 未配置

**错误信息：** `OpenAI API key 未配置`

**解决方法：**
1. 在 `.env` 文件中设置 `OPENAI_API_KEY`
2. 或设置环境变量 `OPENAI_API_KEY`
3. 确保 API Key 格式正确（以 `sk-` 开头）

### 2. OpenAI API Key 无效

**错误信息：** `Invalid API key`

**解决方法：**
1. 检查 API Key 是否正确（以 `sk-` 开头）
2. 检查 API Key 是否有效且有余额
3. 确保 `.env` 文件中的 `OPENAI_API_KEY` 配置正确

### 3. Redis 连接失败

**错误信息：** `Redis connection failed`

**解决方法：**
1. 如果不需要消息队列，设置 `QUEUE_ENABLED=false`
2. 如果需要消息队列：
   - 安装并启动 Redis
   - 检查 `REDIS_URL` 配置是否正确
   - 确保 Redis 服务正在运行

## 验证配置

启动服务后，检查日志确认配置是否正确：

```powershell
python run.py
```

查看日志输出，应该看到：
- `使用 LangChain 1.2.0 兼容层`
- `使用 OpenAI 嵌入模型`
- `应用启动完成`

## 下一步

配置完成后：
1. 启动服务：`python run.py`
2. 访问 API 文档：http://localhost:8000/docs
3. 运行测试：`python test_api.py`

更多信息：
- [快速开始指南](QUICK_START.md)
- [免费 LLM 设置](FREE_LLM_SETUP.md)
- [API 调用示例](API_CALL_EXAMPLES.md)
