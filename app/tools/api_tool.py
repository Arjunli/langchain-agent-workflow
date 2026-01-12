"""API 调用工具"""
import requests
import aiohttp
from typing import Dict, Any, Optional
from app.tools.registry import BaseTool
import logging

logger = logging.getLogger(__name__)


class APICallTool(BaseTool):
    """API 调用工具"""
    
    def __init__(self):
        super().__init__(
            name="api_call",
            description="调用 HTTP API 接口，支持 GET、POST、PUT、DELETE 等方法"
        )
    
    def run(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None,
            timeout: int = 30) -> Dict[str, Any]:
        """执行 API 调用"""
        try:
            headers = headers or {}
            params = params or {}
            
            logger.info(f"调用 API: {method} {url}")
            
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=timeout
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            logger.info(f"API 调用成功: {method} {url}, 状态码: {response.status_code}")
            return result
        
        except Exception as e:
            logger.error(f"API 调用失败: {method} {url}, 错误: {e}")
            return {
                "error": str(e),
                "status_code": 500
            }
    
    async def run_async(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None,
                       params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None,
                       timeout: int = 30) -> Dict[str, Any]:
        """异步执行 API 调用"""
        try:
            headers = headers or {}
            params = params or {}
            
            logger.info(f"异步调用 API: {method} {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    result = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": data
                    }
                    
                    logger.info(f"API 调用成功: {method} {url}, 状态码: {response.status}")
                    return result
        
        except Exception as e:
            logger.error(f"API 调用失败: {method} {url}, 错误: {e}")
            return {
                "error": str(e),
                "status_code": 500
            }

