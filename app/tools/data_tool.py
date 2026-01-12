"""数据处理工具"""
from typing import Dict, Any, List, Optional
from app.tools.registry import BaseTool
import json
import logging

logger = logging.getLogger(__name__)


class DataProcessingTool(BaseTool):
    """数据处理工具"""
    
    def __init__(self):
        super().__init__(
            name="data_processing",
            description="数据处理工具，支持 JSON 解析、数据转换、过滤等操作"
        )
    
    def run(self, operation: str, data: Any, **kwargs) -> Dict[str, Any]:
        """执行数据处理操作"""
        try:
            operation = operation.lower()
            
            if operation == "parse_json":
                if isinstance(data, str):
                    parsed = json.loads(data)
                else:
                    parsed = data
                return {
                    "success": True,
                    "data": parsed
                }
            
            elif operation == "to_json":
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                return {
                    "success": True,
                    "json": json_str
                }
            
            elif operation == "filter":
                # 简单的过滤操作
                filter_key = kwargs.get("key")
                filter_value = kwargs.get("value")
                
                if isinstance(data, list):
                    if filter_key:
                        filtered = [item for item in data if isinstance(item, dict) and item.get(filter_key) == filter_value]
                    else:
                        filtered = data
                    return {
                        "success": True,
                        "data": filtered,
                        "count": len(filtered)
                    }
                else:
                    return {"error": "数据必须是列表类型"}
            
            elif operation == "transform":
                # 简单的转换操作
                transform_type = kwargs.get("type", "uppercase")
                
                if transform_type == "uppercase" and isinstance(data, str):
                    return {
                        "success": True,
                        "data": data.upper()
                    }
                elif transform_type == "lowercase" and isinstance(data, str):
                    return {
                        "success": True,
                        "data": data.lower()
                    }
                else:
                    return {"error": f"不支持的转换类型: {transform_type}"}
            
            elif operation == "extract":
                # 提取字段
                keys = kwargs.get("keys", [])
                if isinstance(data, dict):
                    extracted = {k: data.get(k) for k in keys if k in data}
                    return {
                        "success": True,
                        "data": extracted
                    }
                elif isinstance(data, list):
                    extracted = [{k: item.get(k) for k in keys if k in item} for item in data if isinstance(item, dict)]
                    return {
                        "success": True,
                        "data": extracted
                    }
                else:
                    return {"error": "数据必须是字典或列表类型"}
            
            else:
                return {"error": f"不支持的操作: {operation}"}
        
        except Exception as e:
            logger.error(f"数据处理失败: {operation}, 错误: {e}")
            return {"error": str(e)}

