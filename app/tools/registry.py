"""工具注册表"""
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """执行工具"""
        pass
    
    def __repr__(self):
        return f"<Tool: {self.name}>"


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> list[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """获取所有工具的描述"""
        return {name: tool.description for name, tool in self._tools.items()}

