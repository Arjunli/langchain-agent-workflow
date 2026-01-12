# 日志系统使用指南

## 概述

系统已实现完整的结构化日志管理系统，支持：
- ✅ 请求追踪ID（trace_id）自动注入
- ✅ 线程和协程标识
- ✅ 结构化日志（JSON格式）
- ✅ 日志文件分离（按类型、按日期）
- ✅ 上下文管理（contextvars）

## 核心特性

### 1. 自动追踪ID

每个HTTP请求会自动生成：
- **trace_id**: 追踪ID（可从请求头`X-Trace-Id`传入，否则自动生成）
- **request_id**: 请求ID（自动生成）

这些ID会在整个请求生命周期中自动传递，包括：
- API处理
- 异步任务执行
- Worker处理

### 2. 线程和协程标识

日志中自动包含：
- **线程ID和名称**: 标识执行线程
- **协程ID**: 标识异步协程（如果存在）
- **事件循环ID**: 标识事件循环

### 3. 日志文件分离

日志文件按类型分离：
- `app.log`: 所有日志
- `error.log`: 错误日志（ERROR及以上）
- `access.log`: API访问日志
- `worker.log`: Worker任务处理日志

日志文件按日期轮转（每天午夜）。

### 4. 结构化日志

支持两种格式：
- **JSON格式**: 便于日志聚合和分析（如ELK、Loki）
- **文本格式**: 便于人工阅读

## 配置

在 `.env` 文件中配置：

```env
# 日志级别
LOG_LEVEL=INFO

# 日志目录
LOG_DIR=./logs

# 是否启用文件日志
ENABLE_FILE_LOGGING=true

# 是否启用控制台日志
ENABLE_CONSOLE_LOGGING=true

# 是否使用JSON格式（文件日志）
LOG_JSON_FORMAT=false
```

## 使用方法

### 1. 基本使用

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")
```

### 2. 带上下文的日志

```python
logger.info(
    "处理用户请求",
    extra={
        "user_id": "12345",
        "action": "create_workflow",
        "workflow_id": "wf_001"
    }
)
```

### 3. 异常日志

```python
try:
    # 一些操作
    pass
except Exception as e:
    logger.exception("操作失败", exc_info=True)
    # 或者
    logger.error("操作失败", exc_info=True)
```

### 4. 在异步函数中使用

```python
async def process_task(task_id: str):
    logger = get_logger(__name__)
    
    # trace_id会自动从上下文传递
    logger.info(f"开始处理任务: {task_id}")
    
    # 异步操作
    result = await some_async_operation()
    
    logger.info(f"任务处理完成: {task_id}")
```

### 5. 设置自定义追踪ID

```python
from app.utils.logger import set_trace_id, set_request_id, set_user_id

# 设置追踪ID（通常在中间件中自动完成）
set_trace_id("custom-trace-id-12345")
set_request_id("custom-request-id-67890")
set_user_id("user-123")
```

## 日志格式示例

### JSON格式（文件日志）

```json
{
  "timestamp": "2024-01-01T10:00:00.123456",
  "level": "INFO",
  "logger": "app.api.workflow",
  "message": "执行工作流: wf_001",
  "module": "workflow",
  "function": "execute_workflow",
  "line": 123,
  "thread": {
    "id": 12345,
    "name": "MainThread"
  },
  "coroutine": {
    "id": "140234567890",
    "loop_id": 140234567891
  },
  "context": {
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "660e8400-e29b-41d4-a716-446655440001"
  },
  "extra": {
    "workflow_id": "wf_001",
    "user_id": "user-123"
  }
}
```

### 文本格式（控制台）

```
2024-01-01 10:00:00.123 INFO [trace:550e8400] [req:660e8400] [MainThread] [coro:140234567890] app.api.workflow - 执行工作流: wf_001
```

## 日志文件结构

```
logs/
├── app.log          # 所有日志
├── app.log.2024-01-01  # 历史日志（按日期）
├── error.log        # 错误日志
├── error.log.2024-01-01
├── access.log       # API访问日志
├── access.log.2024-01-01
├── worker.log       # Worker日志
└── worker.log.2024-01-01
```

## 追踪请求流程

### 1. HTTP请求

```bash
# 请求会自动生成trace_id
curl -X POST "http://localhost:8000/api/workflows/wf_001/execute"

# 或者传入自定义trace_id
curl -X POST "http://localhost:8000/api/workflows/wf_001/execute" \
  -H "X-Trace-Id: custom-trace-id-12345"
```

响应头会包含：
```
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000
X-Request-Id: 660e8400-e29b-41d4-a716-446655440001
```

### 2. 异步任务

当创建异步任务时，trace_id会自动传递到任务中：

```python
# 在API中创建任务
task = Task(
    type=TaskType.WORKFLOW_EXECUTE,
    params={...},
    metadata={
        "trace_id": get_trace_id(),  # 自动传递
    }
)
```

### 3. Worker处理

Worker处理任务时，会自动设置trace_id：

```python
# Worker中
if task.metadata.get("trace_id"):
    set_trace_id(task.metadata["trace_id"])

logger.info("处理任务")  # 日志会自动包含trace_id
```

## 日志查询

### 1. 按trace_id查询

```bash
# 查找特定trace_id的所有日志
grep "550e8400" logs/app.log

# JSON格式
cat logs/app.log | jq 'select(.context.trace_id == "550e8400-e29b-41d4-a716-446655440000")'
```

### 2. 按线程查询

```bash
# 查找特定线程的日志
grep "Thread-1" logs/app.log
```

### 3. 按协程查询

```bash
# JSON格式查询协程
cat logs/app.log | jq 'select(.coroutine.id == "140234567890")'
```

### 4. 按时间范围查询

```bash
# 查找特定时间段的日志
grep "2024-01-01 10:" logs/app.log
```

## 最佳实践

### 1. 使用合适的日志级别

- **DEBUG**: 详细的调试信息（开发环境）
- **INFO**: 一般信息（正常操作）
- **WARNING**: 警告信息（潜在问题）
- **ERROR**: 错误信息（需要关注）
- **CRITICAL**: 严重错误（需要立即处理）

### 2. 添加上下文信息

```python
# 好的做法
logger.info(
    "处理工作流",
    extra={
        "workflow_id": workflow_id,
        "user_id": user_id,
        "duration": duration_ms
    }
)

# 不好的做法
logger.info(f"处理工作流 {workflow_id}")
```

### 3. 记录关键操作

- API请求和响应
- 任务创建和完成
- 错误和异常
- 性能关键点

### 4. 避免敏感信息

```python
# 不好的做法
logger.info(f"用户密码: {password}")

# 好的做法
logger.info("用户登录", extra={"user_id": user_id})
```

## 日志聚合和分析

### 1. ELK Stack

如果使用JSON格式，可以直接导入Elasticsearch：

```python
# 配置JSON格式
LOG_JSON_FORMAT=true
```

### 2. Loki

使用Grafana Loki收集日志：

```yaml
# promtail配置
- job_name: agent-logs
  static_configs:
    - targets:
        - localhost
      labels:
        job: agent
        __path__: /path/to/logs/*.log
```

### 3. 自定义分析

使用jq等工具分析JSON日志：

```bash
# 统计错误数量
cat logs/error.log | jq -r '.level' | sort | uniq -c

# 统计API响应时间
cat logs/access.log | jq -r '.extra.process_time' | awk '{sum+=$1; count++} END {print sum/count}'
```

## 故障排查

### 1. 追踪完整请求流程

```bash
# 1. 获取trace_id（从响应头或日志）
TRACE_ID="550e8400-e29b-41d4-a716-446655440000"

# 2. 查找所有相关日志
grep "$TRACE_ID" logs/*.log

# 3. 查看时间线
grep "$TRACE_ID" logs/app.log | jq -r '.timestamp + " " + .level + " " + .message'
```

### 2. 查找错误

```bash
# 查看最近的错误
tail -n 100 logs/error.log

# 查看特定错误的堆栈
grep "Task failed" logs/error.log | jq -r '.exception.traceback'
```

### 3. 性能分析

```bash
# 查找慢请求（假设记录在extra中）
cat logs/access.log | jq 'select(.extra.process_time > 1.0)'
```

## 注意事项

1. **日志文件大小**: 默认每个文件最大10MB，保留5个备份
2. **日志轮转**: 每天午夜自动轮转
3. **上下文传递**: trace_id在异步调用中自动传递（使用contextvars）
4. **性能影响**: 日志记录有性能开销，生产环境建议使用INFO级别
5. **磁盘空间**: 定期清理旧日志文件

## 示例：完整请求追踪

```bash
# 1. 发送请求
curl -X POST "http://localhost:8000/api/workflows/wf_001/execute" \
  -H "X-Trace-Id: my-trace-123"

# 响应头
X-Trace-Id: my-trace-123
X-Request-Id: 660e8400-e29b-41d4-a716-446655440001

# 2. 查询日志
grep "my-trace-123" logs/*.log

# 输出示例：
# access.log: Request started: POST /api/workflows/wf_001/execute
# app.log: 创建任务: task_001
# worker.log: 开始处理任务: task_001
# worker.log: 任务处理完成: task_001
# access.log: Request completed: POST /api/workflows/wf_001/execute
```

这样就能完整追踪一个请求从API到Worker的整个流程！



