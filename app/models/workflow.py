"""工作流定义模型"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class NodeType(str, Enum):
    """节点类型"""
    TASK = "task"  # 任务节点
    CONDITION = "condition"  # 条件节点
    LOOP = "loop"  # 循环节点
    PARALLEL = "parallel"  # 并行节点
    START = "start"  # 开始节点
    END = "end"  # 结束节点


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    SKIPPED = "skipped"  # 已跳过


class Edge(BaseModel):
    """工作流边（连接）"""
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    condition: Optional[str] = Field(None, description="条件表达式（可选）")


class Node(BaseModel):
    """工作流节点"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    type: NodeType = Field(..., description="节点类型")
    description: Optional[str] = Field(None, description="节点描述")
    
    # 任务配置
    tool_name: Optional[str] = Field(None, description="工具名称")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    
    # 条件节点配置
    condition_expr: Optional[str] = Field(None, description="条件表达式")
    
    # 循环节点配置
    loop_var: Optional[str] = Field(None, description="循环变量名")
    loop_items: Optional[str] = Field(None, description="循环项表达式")
    
    # 并行节点配置
    parallel_branches: Optional[List[List[str]]] = Field(None, description="并行分支节点ID列表")
    
    # 执行状态
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点状态")
    result: Optional[Any] = Field(None, description="节点执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class Workflow(BaseModel):
    """工作流定义"""
    id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: str = Field(default="1.0.0", description="版本号")
    
    # 工作流结构
    nodes: List[Node] = Field(default_factory=list, description="节点列表")
    edges: List[Edge] = Field(default_factory=list, description="边列表")
    
    # 执行状态
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="工作流状态")
    current_node_id: Optional[str] = Field(None, description="当前执行节点ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="工作流变量")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def get_start_node(self) -> Optional[Node]:
        """获取开始节点"""
        for node in self.nodes:
            if node.type == NodeType.START:
                return node
        return None
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """根据ID获取节点"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_next_nodes(self, node_id: str) -> List[Node]:
        """获取下一个节点列表"""
        next_node_ids = [edge.target for edge in self.edges if edge.source == node_id]
        return [node for node in self.nodes if node.id in next_node_ids]
    
    def get_previous_nodes(self, node_id: str) -> List[Node]:
        """获取上一个节点列表"""
        prev_node_ids = [edge.source for edge in self.edges if edge.target == node_id]
        return [node for node in self.nodes if node.id in prev_node_ids]

