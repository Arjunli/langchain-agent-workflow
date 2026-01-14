# 快速启动指南

## 前置要求

1. **Python 3.8+**
2. **OpenAI API Key**（必需，用于LLM调用）
3. **Redis**（可选，如果启用消息队列）

## 步骤1: 检查Python版本

```powershell
python --version
# 或
py --version
```

确保版本 >= 3.8

## 步骤2: 安装依赖

```powershell
# 使用pip安装所有依赖
pip install -r requirements.txt

# 如果pip不可用，使用py
py -m pip install -r requirements.txt

# 如果遇到权限问题，使用--user
pip install -r requirements.txt --user
```

## 步骤3: 配置环境变量

创建 `.env` 文件（在项目根目录）：

```powershell
# 如果已有.env文件，可以跳过
# 如果没有，创建新文件
New-Item -Path .env -ItemType File -Force
```

编辑 `.env` 文件，添加以下配置：

```env
# OpenAI API 配置（必需）
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# 消息队列配置（可选）
QUEUE_ENABLED=false
# 如果设置为false，将使用同步执行模式，不需要Redis

# Redis配置（仅在启用消息队列时需要）
# REDIS_URL=redis://localhost:6379/0

# 日志配置（可选）
LOG_LEVEL=INFO
LOG_DIR=./logs
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true
```

**重要**: 将 `your_openai_api_key_here` 替换为你的实际 OpenAI API Key

## 步骤4: 启动服务

### 方式1: 使用启动脚本（推荐）

```powershell
python run.py
```

### 方式2: 使用uvicorn直接启动

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式3: Windows使用py命令

```powershell
py run.py
```

## 步骤5: 验证服务运行

服务启动后，访问以下地址：

- **API文档（Swagger UI）**: http://localhost:8000/docs
- **API文档（ReDoc）**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## 步骤6: 测试聊天接口（可选）

使用浏览器访问 http://localhost:8000/docs，在Swagger UI中测试 `/api/chat` 接口。

或使用PowerShell测试：

```powershell
# 测试聊天接口
$body = @{
    message = "你好，介绍一下你自己"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## 可选：启动Worker（如果需要消息队列）

如果启用了消息队列（`QUEUE_ENABLED=true`），需要单独启动Worker：

```powershell
# 在新终端窗口运行
python run_worker.py
```

## 常见问题

### 1. 缺少依赖包

如果提示缺少某个包，单独安装：

```powershell
pip install <package_name>
```

### 2. OpenAI API Key未配置

确保 `.env` 文件中有正确的 `OPENAI_API_KEY`，并且文件在项目根目录。

### 3. 端口被占用

如果8000端口被占用，可以修改 `run.py` 中的端口号，或使用：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Redis连接失败

如果启用了消息队列但Redis未运行，系统会自动降级到同步模式。要使用消息队列功能，需要：

1. 安装Redis（Windows可以使用WSL或Docker）
2. 启动Redis服务
3. 确保 `REDIS_URL` 配置正确

### 5. 导入错误

如果遇到导入错误，确保：
- 在项目根目录运行
- Python路径正确
- 所有依赖已安装

## 开发模式

启动时会自动启用热重载（`reload=True`），修改代码后会自动重启服务。

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [USAGE.md](USAGE.md) 了解详细使用方法
- 查看 [API_RESPONSE_FORMAT.md](API_RESPONSE_FORMAT.md) 了解API响应格式
- 访问 http://localhost:8000/docs 查看交互式API文档
