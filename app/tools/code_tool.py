"""代码执行工具（可选，需沙箱环境）"""
from typing import Dict, Any, Optional
from app.tools.registry import BaseTool
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


class CodeExecutionTool(BaseTool):
    """代码执行工具（注意：生产环境需要沙箱环境）"""
    
    def __init__(self):
        super().__init__(
            name="code_execution",
            description="执行 Python 代码（注意：仅用于安全环境，生产环境需要沙箱）"
        )
    
    def run(self, code: str, language: str = "python", timeout: int = 30) -> Dict[str, Any]:
        """执行代码"""
        if language != "python":
            return {"error": f"不支持的语言: {language}"}
        
        # 使用context manager确保临时文件总是被清理
        from contextlib import contextmanager
        
        @contextmanager
        def temp_code_file(code: str):
            """临时代码文件管理器"""
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(code)
                    tmp_path = tmp.name
                yield tmp_path
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                        logger.debug(f"临时代码文件已清理: {tmp_path}")
                    except Exception as e:
                        logger.warning(f"清理临时代码文件失败: {tmp_path}, 错误: {e}")
        
        try:
            with temp_code_file(code) as tmp_path:
                # 执行代码（注意：生产环境应该使用沙箱）
                result = subprocess.run(
                    ["python", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
        
        except subprocess.TimeoutExpired:
            return {"error": f"代码执行超时（>{timeout}秒）"}
        except Exception as e:
            logger.error(f"代码执行失败: {e}", exc_info=True)
            return {"error": str(e)}

