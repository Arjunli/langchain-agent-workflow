"""FastAPI依赖注入"""
from fastapi import Request
from typing import Optional

def get_request(request: Request) -> Request:
    """获取Request对象（依赖注入）"""
    return request
