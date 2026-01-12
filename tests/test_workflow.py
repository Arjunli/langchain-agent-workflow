"""工作流测试"""
import pytest
from app.models.workflow import Workflow, Node, Edge, NodeType, NodeStatus


def test_workflow_creation():
    """测试工作流创建"""
    workflow = Workflow(
        id="test_workflow",
        name="测试工作流",
        description="这是一个测试工作流",
        nodes=[
            Node(id="start", name="开始", type=NodeType.START),
            Node(id="task1", name="任务1", type=NodeType.TASK, tool_name="api_call"),
            Node(id="end", name="结束", type=NodeType.END)
        ],
        edges=[
            Edge(source="start", target="task1"),
            Edge(source="task1", target="end")
        ]
    )
    
    assert workflow.id == "test_workflow"
    assert len(workflow.nodes) == 3
    assert len(workflow.edges) == 2


def test_workflow_get_start_node():
    """测试获取开始节点"""
    workflow = Workflow(
        id="test",
        name="测试",
        nodes=[
            Node(id="start", name="开始", type=NodeType.START),
            Node(id="task", name="任务", type=NodeType.TASK)
        ],
        edges=[]
    )
    
    start_node = workflow.get_start_node()
    assert start_node is not None
    assert start_node.id == "start"

