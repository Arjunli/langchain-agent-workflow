# 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少需要配置 OpenAI API Key：

```env
OPENAI_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
python run.py
```

或者使用 uvicorn 直接启动：

```bash
uvicorn app.main:app --reload
```

服务启动后，访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 使用示例

### 1. 聊天接口

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我执行数据分析工作流",
    "stream": false
  }'
```

### 2. 创建工作流

```bash
curl -X POST "http://localhost:8000/api/workflows" \
  -H "Content-Type: application/json" \
  -d @examples/workflow_example.json
```

### 3. 上传工作流文件

```bash
curl -X POST "http://localhost:8000/api/workflows/upload" \
  -F "file=@examples/workflow_example.yaml"
```

### 4. 列出所有工作流

```bash
curl "http://localhost:8000/api/workflows"
```

### 5. 执行工作流

```bash
curl -X POST "http://localhost:8000/api/workflows/{workflow_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "key": "value"
    }
  }'
```

### 6. 搜索工作流

```bash
curl "http://localhost:8000/api/workflows/search/数据分析"
```

## WebSocket 使用

### JavaScript 示例

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "帮我执行工作流"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到响应:', data);
};
```

## 工作流定义格式

### YAML 格式示例

```yaml
id: my_workflow
name: 我的工作流
description: 工作流描述
version: "1.0.0"

nodes:
  - id: start
    name: 开始
    type: start
  
  - id: task1
    name: 任务1
    type: task
    tool_name: api_call
    tool_params:
      url: "https://api.example.com"
      method: "GET"
  
  - id: end
    name: 结束
    type: end

edges:
  - source: start
    target: task1
  - source: task1
    target: end
```

### 节点类型

- `start`: 开始节点
- `end`: 结束节点
- `task`: 任务节点（调用工具）
- `condition`: 条件节点（分支判断）
- `loop`: 循环节点
- `parallel`: 并行节点

### 可用工具

- `api_call`: API 调用工具
- `file_operation`: 文件操作工具
- `data_processing`: 数据处理工具
- `code_execution`: 代码执行工具（需谨慎使用）

## 注意事项

1. **代码执行工具**: `code_execution` 工具在生产环境需要沙箱环境，默认未启用
2. **异步执行**: 工作流执行是异步的，长时间运行的工作流建议使用 WebSocket 获取实时状态
3. **变量替换**: 工作流支持变量替换，使用 `${variable_name}` 格式
4. **错误处理**: 工作流执行失败时会记录错误信息，可以通过 API 查询状态

## 开发建议

1. 使用虚拟环境管理依赖
2. 开发时启用 `reload` 模式自动重载
3. 查看日志了解工作流执行详情
4. 使用 Swagger UI 测试 API 接口

