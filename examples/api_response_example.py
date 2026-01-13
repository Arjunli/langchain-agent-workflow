"""统一API响应格式使用示例"""
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.models.response import BaseResponse, ResponseCode
from app.utils.response import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    paginated_response
)

app = FastAPI()


# 示例1: 成功响应
@app.get("/example/success")
async def example_success(request: Request):
    """示例：返回成功响应"""
    data = {"user_id": "123", "name": "张三"}
    return success_response(
        data=data,
        message="操作成功",
        request=request
    )


# 示例2: 创建资源响应
@app.post("/example/create")
async def example_create(request: Request):
    """示例：创建资源响应"""
    data = {"id": "new_123", "name": "新资源"}
    return created_response(
        data=data,
        message="资源创建成功",
        request=request
    )


# 示例3: 分页响应
@app.get("/example/list")
async def example_list(request: Request, page: int = 1, page_size: int = 10):
    """示例：分页响应"""
    # 模拟数据
    all_data = [{"id": i, "name": f"项目{i}"} for i in range(1, 101)]
    total = len(all_data)
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    page_data = all_data[start:end]
    
    return paginated_response(
        data=page_data,
        page=page,
        page_size=page_size,
        total=total,
        message="获取列表成功",
        request=request
    )


# 示例4: 错误响应
@app.get("/example/error")
async def example_error(request: Request):
    """示例：错误响应"""
    return error_response(
        message="资源不存在",
        code=ResponseCode.NOT_FOUND,
        request=request
    )


# 示例5: 资源不存在响应
@app.get("/example/not-found/{resource_id}")
async def example_not_found(resource_id: str, request: Request):
    """示例：资源不存在响应"""
    # 模拟检查资源
    if resource_id != "123":
        return not_found_response(
            resource=f"资源 {resource_id}",
            request=request
        )
    
    return success_response(
        data={"id": resource_id, "name": "找到的资源"},
        request=request
    )


# 测试代码
if __name__ == "__main__":
    client = TestClient(app)
    
    # 测试成功响应
    print("=== 测试成功响应 ===")
    response = client.get("/example/success")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # 测试创建响应
    print("=== 测试创建响应 ===")
    response = client.post("/example/create")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # 测试分页响应
    print("=== 测试分页响应 ===")
    response = client.get("/example/list?page=1&page_size=5")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # 测试错误响应
    print("=== 测试错误响应 ===")
    response = client.get("/example/error")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # 测试资源不存在
    print("=== 测试资源不存在 ===")
    response = client.get("/example/not-found/999")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
