# 统一API响应格式文档

## 概述

系统已实现统一的API响应格式，所有API端点都返回标准化的响应结构，便于前端处理和错误处理。

## 响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 实际数据
  },
  "timestamp": "2024-01-01T10:00:00.123456",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### 错误响应

```json
{
  "code": 404,
  "message": "resource not found",
  "errors": [
    {
      "field": "workflow_id",
      "message": "工作流不存在",
      "code": "not_found"
    }
  ],
  "timestamp": "2024-01-01T10:00:00.123456",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "660e8400-e29b-41d4-a716-446655440001",
  "path": "/api/workflows/123"
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": [
    // 数据列表
  ],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total": 100,
    "total_pages": 10
  },
  "timestamp": "2024-01-01T10:00:00.123456",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

## 状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 查询、更新操作成功 |
| 201 | 创建成功 | 创建资源成功 |
| 202 | 已接受 | 异步任务已接受 |
| 400 | 请求错误 | 参数错误、业务逻辑错误 |
| 401 | 未授权 | 需要认证 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 资源不存在 | 资源未找到 |
| 409 | 冲突 | 资源冲突（如重复创建） |
| 422 | 验证错误 | 请求参数验证失败 |
| 500 | 服务器错误 | 内部服务器错误 |
| 503 | 服务不可用 | 服务暂时不可用 |
| 504 | 超时 | 请求超时 |

## 使用示例

### 在API端点中使用

```python
from fastapi import Request
from app.utils.response import success_response, created_response, not_found_response
from app.models.response import BaseResponse

@router.get("/example", response_model=BaseResponse[Dict[str, Any]])
async def example(request: Request):
    # 成功响应
    return success_response(
        data={"result": "ok"},
        message="操作成功",
        request=request
    )
    
    # 创建资源响应
    return created_response(
        data=new_resource,
        message="资源创建成功",
        request=request
    )
    
    # 资源不存在
    return not_found_response(
        resource="工作流 wf_001",
        request=request
    )
```

### 响应工具函数

#### success_response()
创建成功响应

```python
success_response(
    data=any_data,           # 响应数据
    message="success",       # 响应消息
    code=ResponseCode.SUCCESS,  # 状态码（可选）
    request=request          # Request对象（可选，用于获取trace_id）
)
```

#### created_response()
创建资源成功响应（状态码201）

```python
created_response(
    data=new_resource,
    message="created",
    request=request
)
```

#### error_response()
创建错误响应

```python
error_response(
    message="error message",
    code=ResponseCode.NOT_FOUND,
    errors=[ErrorDetail(...)],  # 详细错误列表（可选）
    request=request,
    path="/api/example"        # 请求路径（可选）
)
```

#### not_found_response()
资源不存在响应

```python
not_found_response(
    resource="工作流 wf_001",
    request=request
)
```

#### paginated_response()
分页响应

```python
paginated_response(
    data=[...],              # 数据列表
    page=1,                  # 当前页码
    page_size=10,            # 每页数量
    total=100,               # 总数量
    message="success",
    request=request
)
```

## 异常处理

系统已配置全局异常处理器，自动捕获并转换为统一格式：

- **Exception**: 所有未捕获的异常
- **HTTPException**: HTTP异常
- **RequestValidationError**: 请求验证错误

所有异常都会自动：
- 记录日志（包含trace_id）
- 转换为统一错误响应格式
- 包含追踪信息

## 迁移指南

### 旧格式（已废弃）

```python
@router.get("/example")
async def example():
    return {"result": "ok"}  # 直接返回数据
```

### 新格式（推荐）

```python
@router.get("/example", response_model=BaseResponse[Dict[str, Any]])
async def example(request: Request):
    return success_response(
        data={"result": "ok"},
        message="操作成功",
        request=request
    )
```

## 优势

1. **统一格式**: 所有API返回格式一致，便于前端处理
2. **错误追踪**: 自动包含trace_id和request_id，便于问题定位
3. **类型安全**: 使用Pydantic模型，类型检查更严格
4. **自动处理**: 异常自动转换为统一格式
5. **易于扩展**: 可以轻松添加新的响应类型

## 注意事项

1. **Request参数**: 必须作为函数参数传入，不能有默认值
2. **response_model**: 建议在路由装饰器中指定，便于API文档生成
3. **向后兼容**: 旧代码仍可使用，但建议逐步迁移
4. **流式响应**: 流式接口（如SSE）不使用统一格式

## 示例：完整API端点

```python
from fastapi import APIRouter, Request
from app.models.response import BaseResponse
from app.utils.response import (
    success_response,
    created_response,
    not_found_response,
    internal_error_response
)

router = APIRouter()

@router.get("/items/{item_id}", response_model=BaseResponse[Dict[str, Any]])
async def get_item(item_id: str, request: Request):
    """获取项目"""
    try:
        item = get_item_from_db(item_id)
        if not item:
            return not_found_response(
                resource=f"项目 {item_id}",
                request=request
            )
        
        return success_response(
            data=item,
            message="获取项目成功",
            request=request
        )
    except Exception as e:
        logger.error(f"获取项目失败: {e}", exc_info=True)
        return internal_error_response(
            message=f"获取项目失败: {str(e)}",
            request=request
        )
```
