# 免费 LLM 设置指南

## 使用 Ollama（推荐 - 完全免费）

Ollama 是一个免费的本地 LLM 运行工具，支持多种开源模型。

### 1. 安装 Ollama

**Windows:**
1. 访问 https://ollama.ai
2. 下载并安装 Ollama
3. 安装完成后，Ollama 会自动启动

**验证安装:**
```powershell
ollama --version
```

### 2. 下载模型

```powershell
# 下载 Llama 2（推荐，7B 模型，约 4GB）
ollama pull llama2

# 或其他模型：
ollama pull mistral      # Mistral（更小更快）
ollama pull qwen         # Qwen（中文友好）
ollama pull chatglm      # ChatGLM（中文友好）
ollama pull codellama    # Code Llama（代码专用）
```

### 3. 配置 .env 文件

在项目根目录的 `.env` 文件中添加：

```env
# 使用 Ollama（免费）
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# 不需要 OpenAI API key
```

### 4. 安装 Python 依赖

```powershell
pip install langchain-ollama
```

### 5. 启动服务

```powershell
python run.py
```

## 其他免费选项

### Groq API（免费额度）

1. 注册账号：https://console.groq.com
2. 获取免费 API key
3. 配置 `.env`：

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama2-70b-4096
```

（需要添加 Groq 支持代码）

## 注意事项

1. **Ollama 需要本地运行**：首次使用需要下载模型（几GB大小）
2. **性能**：本地 LLM 速度取决于你的硬件配置
3. **内存**：建议至少 8GB RAM，推荐 16GB+
4. **GPU**：如果有 NVIDIA GPU，Ollama 会自动使用加速

## 模型推荐

- **Llama 2**：通用模型，平衡性能和效果
- **Mistral**：更小更快，适合快速响应
- **Qwen/ChatGLM**：中文友好，适合中文对话
- **Code Llama**：代码生成专用

## 故障排除

### Ollama 连接失败

```powershell
# 检查 Ollama 是否运行
ollama list

# 重启 Ollama
# Windows: 在任务管理器中重启 Ollama 服务
```

### 模型未找到

```powershell
# 查看已安装的模型
ollama list

# 如果模型不存在，下载它
ollama pull llama2
```
