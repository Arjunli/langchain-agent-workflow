# 消息队列使用指南

## 概述

系统已集成基于Redis的消息队列，用于异步处理耗时任务，提高系统并发处理能力。

## 功能特性

- ✅ 异步任务执行（工作流执行）
- ✅ 任务状态查询
- ✅ 任务取消
- ✅ 自动重试机制
- ✅ 队列统计信息
- ✅ 多Worker并发处理

## 配置

### 1. 安装Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# 下载并安装: https://github.com/microsoftarchive/redis/releases
```

### 2. 启动Redis

```bash
# Linux/macOS
redis-server

# Windows
redis-server.exe
```

### 3. 配置环境变量

在 `.env` 文件中添加：

```env
# Redis配置
REDIS_URL=redis://localhost:6379/0

# 消息队列配置
QUEUE_ENABLED=true
MAX_WORKERS=5
```

## 使用方式

### 1. 启动API服务

```bash
python run.py
```

### 2. 启动Worker（单独进程）

```bash
python run_worker.py
```

**注意**: Worker需要单独启动，可以启动多个Worker实例来提高处理能力。

### 3. 异步执行工作流

#### 方式1: 使用API（推荐）

```bash
# 异步执行工作流
curl -X POST "http://localhost:8000/api/workflows/{workflow_id}/execute?async_execute=true" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "param1": "value1"
    }
  }'
```

响应示例：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "工作流已加入执行队列",
  "workflow_id": "my_workflow"
}
```

#### 方式2: 同步执行（降级）

如果消息队列不可用，系统会自动降级到同步执行：

```bash
curl -X POST "http://localhost:8000/api/workflows/{workflow_id}/execute?async_execute=false" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {}
  }'
```

### 4. 查询任务状态

```bash
curl "http://localhost:8000/api/workflows/tasks/{task_id}"
```

响应示例：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow_execute",
  "status": "completed",
  "created_at": "2024-01-01T10:00:00",
  "started_at": "2024-01-01T10:00:01",
  "completed_at": "2024-01-01T10:00:05",
  "result": {
    "workflow_id": "my_workflow",
    "status": "completed",
    "variables": {}
  },
  "error": null,
  "retry_count": 0,
  "max_retries": 3
}
```

### 5. 取消任务

```bash
curl -X POST "http://localhost:8000/api/workflows/tasks/{task_id}/cancel"
```

**注意**: 只能取消处于 `pending` 或 `queued` 状态的任务。

### 6. 查看队列统计

```bash
curl "http://localhost:8000/api/workflows/queue/stats"
```

响应示例：
```json
{
  "enabled": true,
  "queues": {
    "workflow_execute": {
      "queue_length": 5
    },
    "chat_process": {
      "queue_length": 0
    },
    "knowledge_search": {
      "queue_length": 0
    }
  }
}
```

## 任务状态

任务有以下状态：

- `pending`: 等待处理（刚创建）
- `queued`: 已入队（等待Worker处理）
- `running`: 执行中
- `completed`: 已完成
- `failed`: 执行失败
- `cancelled`: 已取消

## 重试机制

任务执行失败时会自动重试，默认最多重试3次。可以通过任务的 `max_retries` 参数配置。

## 高并发场景

### 1. 水平扩展Worker

启动多个Worker进程：

```bash
# Terminal 1
python run_worker.py

# Terminal 2
python run_worker.py

# Terminal 3
python run_worker.py
```

### 2. 使用进程管理器

使用 `supervisor` 或 `systemd` 管理多个Worker：

```ini
# supervisor配置示例
[program:worker]
command=python run_worker.py
directory=/path/to/agent
autostart=true
autorestart=true
numprocs=5
process_name=worker-%(process_num)s
```

### 3. Docker部署

```dockerfile
# Dockerfile示例
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 启动Worker
CMD ["python", "run_worker.py"]
```

```yaml
# docker-compose.yml示例
version: '3.8'
services:
  api:
    build: .
    command: python run.py
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  worker:
    build: .
    command: python run_worker.py
    deploy:
      replicas: 5
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 监控和日志

### 查看Worker日志

Worker会输出详细的日志信息，包括：
- 任务入队/出队
- 任务执行状态
- 错误信息
- 重试信息

### 监控指标

可以通过队列统计API监控：
- 队列长度
- 任务处理速度
- 失败率

## 故障处理

### 1. Redis连接失败

如果Redis不可用，系统会自动降级到同步执行模式，不会影响基本功能。

### 2. Worker崩溃

Worker进程崩溃后，队列中的任务会保留，重启Worker后会自动继续处理。

### 3. 任务堆积

如果队列中任务过多，可以：
- 增加Worker数量
- 优化任务处理逻辑
- 增加Redis内存

## 最佳实践

1. **生产环境**: 始终启用消息队列，使用异步执行
2. **开发环境**: 可以禁用消息队列，使用同步执行便于调试
3. **监控**: 定期检查队列长度，及时发现问题
4. **扩展**: 根据负载情况动态调整Worker数量
5. **错误处理**: 合理设置重试次数，避免无限重试

## 注意事项

1. Worker需要单独启动，不能和API服务在同一个进程中
2. 确保Redis服务稳定运行
3. 任务结果会保留7天，过期后自动删除
4. 大量任务时注意Redis内存使用情况



