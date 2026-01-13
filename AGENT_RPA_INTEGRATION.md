# Agent 和 RPA 模块集成说明

## 概述

本文档说明 Agent 模块和 RPA 模块之间的集成情况。通过创建 RPA 工具，Agent 现在可以调用 RPA 模块的功能来处理 Excel、PDF、Web 等文件。

## 集成状态

✅ **已完成集成**

- Agent 模块现在可以通过 `rpa_process` 工具调用 RPA 模块
- RPA 工具已自动注册到 Agent 的工具注册表中
- 支持同步和异步两种调用方式

## 实现细节

### 1. RPA 工具 (`agent/app/tools/rpa_tool.py`)

创建了 `RPATool` 类，继承自 `BaseTool`，提供以下功能：

- **工具名称**: `rpa_process`
- **工具描述**: "RPA 文件处理工具，支持处理 Excel、PDF、Web 等文件类型。可以自动识别文件类型并使用相应的插件进行处理。"
- **主要方法**:
  - `run()`: 同步执行 RPA 文件处理
  - `run_async()`: 异步执行 RPA 文件处理

### 2. 自动注册

在 `agent/app/main.py` 中，RPA 工具会在应用启动时自动注册：

```python
try:
    tool_registry.register(RPATool())
    logger.info("RPA 工具已注册")
except Exception as e:
    logger.warning(f"RPA 工具注册失败: {e}，RPA 功能将不可用")
```

### 3. 路径解析

RPA 工具会自动解析项目结构，找到 RPA 模块：

- 从 `agent/app/tools/rpa_tool.py` 向上查找项目根目录
- 在项目根目录下查找 `rpa/` 目录
- 将 RPA 模块路径添加到 `sys.path` 中

## 使用方法

### 1. 通过 Agent 聊天接口调用

Agent 现在可以通过自然语言调用 RPA 功能：

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请帮我处理这个 Excel 文件: /path/to/file.xlsx"
  }'
```

### 2. 在工作流中使用

可以在工作流定义中使用 `rpa_process` 工具：

```yaml
nodes:
  - id: rpa_task
    name: 处理文件
    type: task
    tool_name: rpa_process
    tool_params:
      file_path: "${input_file_path}"
      options:
        # 可选的处理选项
```

### 3. 直接调用工具

```python
from app.tools import tool_registry

rpa_tool = tool_registry.get_tool("rpa_process")
result = rpa_tool.run(
    file_path="/path/to/file.xlsx",
    options={"key": "value"}  # 可选
)
```

## 工具参数

### `run()` 和 `run_async()` 参数

- **file_path** (str, 必需): 要处理的文件路径
- **options** (dict, 可选): 处理选项字典

### 返回结果

```python
{
    "success": True,  # 或 False
    "status": "success",  # 或 "error"
    "result": {
        # RPA 模块返回的详细结果
        "status": "success",
        "results": [...],
        ...
    },
    "trace_id": "trace-xxx",
    "request_id": "req-xxx",
    "file_path": "/absolute/path/to/file.xlsx"
}
```

## 错误处理

如果 RPA 模块不可用或处理失败，工具会返回错误信息：

```python
{
    "error": "错误描述",
    "status": "error",
    "file_path": "/path/to/file.xlsx"  # 如果可用
}
```

## 注意事项

1. **路径要求**: 确保项目结构为：
   ```
   langchain/
   ├── agent/
   │   └── app/
   │       └── tools/
   │           └── rpa_tool.py
   └── rpa/
       └── main.py
   ```

2. **依赖安装**: 确保 RPA 模块的依赖已安装（见 `rpa/requirements.txt`）

3. **初始化**: RPA 模块会在首次调用时自动初始化

4. **异步环境**: 在异步环境中（如 FastAPI），建议使用 `run_async()` 方法

5. **文件路径**: 工具会自动将相对路径转换为绝对路径

## 测试

### 检查工具是否注册

```bash
curl "http://localhost:8000/api/tools"  # 如果存在此接口
```

或在代码中：

```python
from app.tools import tool_registry

tools = tool_registry.list_tools()
rpa_tool = tool_registry.get_tool("rpa_process")
if rpa_tool:
    print("RPA 工具已注册")
else:
    print("RPA 工具未注册")
```

### 测试调用

```python
from app.tools import tool_registry

rpa_tool = tool_registry.get_tool("rpa_process")
if rpa_tool:
    result = rpa_tool.run(file_path="test.xlsx")
    print(result)
```

## 日志

RPA 工具会记录以下日志：

- 路径添加成功/失败
- RPA 模块初始化成功/失败
- 文件处理开始/完成
- 错误信息

查看日志：

```bash
# Agent 日志
tail -f agent/logs/app.log

# RPA 日志
tail -f rpa/logs/app.log
```

## 故障排除

### 问题：RPA 工具未注册

**可能原因**:
- RPA 模块路径不正确
- RPA 模块初始化失败

**解决方法**:
1. 检查项目结构是否正确
2. 查看 Agent 启动日志，确认是否有 RPA 工具注册的警告
3. 检查 RPA 模块的依赖是否已安装

### 问题：导入错误

**可能原因**:
- RPA 模块路径未正确添加到 sys.path
- RPA 模块缺少依赖

**解决方法**:
1. 检查日志中的路径信息
2. 确保 RPA 模块的所有依赖已安装
3. 手动测试 RPA 模块是否可以独立运行

### 问题：文件处理失败

**可能原因**:
- 文件不存在
- 文件类型不支持
- RPA 插件未正确配置

**解决方法**:
1. 检查文件路径是否正确
2. 查看 RPA 模块的日志
3. 确认 RPA 插件已正确注册

## 未来改进

- [ ] 添加更多 RPA 工具方法（如批量处理）
- [ ] 支持 RPA 配置的传递
- [ ] 添加 RPA 处理进度回调
- [ ] 支持 RPA 结果的缓存
- [ ] 添加 RPA 工具的使用统计

## 相关文档

- [Agent README](README.md)
- [RPA README](../rpa/README.md)
- [工具使用指南](USAGE.md)
