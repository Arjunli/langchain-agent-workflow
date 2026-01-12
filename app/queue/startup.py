"""队列启动脚本"""
import asyncio
from typing import Optional
from app.queue.manager import QueueManager
from app.queue.worker import TaskWorker
from app.workflows.engine import WorkflowEngine
from app.workflows.registry import WorkflowRegistry
from app.tools import tool_registry
from app.config import settings
from app.utils.logger import setup_logging, get_logger
import signal
import sys

# 设置日志系统
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    enable_file_logging=settings.enable_file_logging,
    enable_console_logging=settings.enable_console_logging,
    json_format=settings.log_json_format,
)

logger = get_logger(__name__)

# 全局变量
worker: Optional[TaskWorker] = None


async def main():
    """主函数"""
    global worker
    
    logger.info("正在启动任务Worker...")
    
    # 初始化组件
    workflow_registry = WorkflowRegistry()
    workflow_engine = WorkflowEngine(workflow_registry, tool_registry)
    queue_manager = QueueManager()
    
    # 创建Worker
    worker = TaskWorker(
        queue_manager=queue_manager,
        workflow_engine=workflow_engine,
        max_workers=settings.max_workers
    )
    
    # 启动Worker
    await worker.start()
    
    logger.info("任务Worker已启动，等待任务...")
    
    # 等待信号
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭Worker...")
    finally:
        await worker.stop()
        logger.info("Worker已关闭")


def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("收到停止信号")
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已停止")

