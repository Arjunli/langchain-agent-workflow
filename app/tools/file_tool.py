"""文件操作工具"""
from pathlib import Path
from typing import Dict, Any, Optional
from app.tools.registry import BaseTool
import json
import logging

logger = logging.getLogger(__name__)


class FileOperationTool(BaseTool):
    """文件操作工具"""
    
    def __init__(self):
        super().__init__(
            name="file_operation",
            description="文件操作工具，支持读取、写入、删除文件等操作"
        )
    
    def run(self, operation: str, file_path: str, content: Optional[str] = None,
            encoding: str = "utf-8") -> Dict[str, Any]:
        """执行文件操作"""
        try:
            path = Path(file_path)
            operation = operation.lower()
            
            if operation == "read":
                if not path.exists():
                    return {"error": f"文件不存在: {file_path}"}
                
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "content": content,
                    "size": len(content)
                }
            
            elif operation == "write":
                # 确保目录存在
                path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content or "")
                
                return {
                    "success": True,
                    "message": f"文件已写入: {file_path}"
                }
            
            elif operation == "delete":
                if not path.exists():
                    return {"error": f"文件不存在: {file_path}"}
                
                path.unlink()
                return {
                    "success": True,
                    "message": f"文件已删除: {file_path}"
                }
            
            elif operation == "exists":
                return {
                    "success": True,
                    "exists": path.exists()
                }
            
            elif operation == "list":
                if not path.exists():
                    return {"error": f"路径不存在: {file_path}"}
                
                if path.is_dir():
                    files = [f.name for f in path.iterdir()]
                    return {
                        "success": True,
                        "files": files
                    }
                else:
                    return {"error": f"不是目录: {file_path}"}
            
            else:
                return {"error": f"不支持的操作: {operation}"}
        
        except Exception as e:
            logger.error(f"文件操作失败: {operation} {file_path}, 错误: {e}")
            return {"error": str(e)}

