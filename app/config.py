"""配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # API 配置
    api_title: str = "LangChain Agent 工作流系统"
    api_version: str = "0.1.0"
    api_description: str = "基于 LangChain 的 Agent 系统，支持通过文字聊天调用复杂工作流"
    
    # LLM 配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7
    llm_max_retries: int = 3  # LLM调用最大重试次数
    llm_retry_delay: float = 1.0  # LLM重试延迟（秒）
    llm_stream_timeout: int = 300  # LLM流式响应超时（秒）
    llm_save_partial: bool = True  # 是否保存部分响应（用于中断恢复）
    
    # 数据库配置
    database_url: str = "sqlite:///./workflows.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # 工作流配置
    workflow_timeout: int = 3600  # 工作流超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    
    # 消息队列配置
    queue_enabled: bool = True  # 是否启用消息队列
    max_workers: int = 5  # 最大worker数量
    
    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "./logs"  # 日志目录
    enable_file_logging: bool = True  # 是否启用文件日志
    enable_console_logging: bool = True  # 是否启用控制台日志
    log_json_format: bool = False  # 是否使用JSON格式（文件日志）
    
    # 缓存配置
    max_conversations: int = 1000  # 最大对话缓存数
    conversation_ttl: int = 3600  # 对话TTL（秒）
    max_vector_stores: int = 50  # 最大向量存储缓存数
    task_timeout: int = 3600  # 任务超时时间（秒）
    websocket_timeout: int = 300  # WebSocket超时时间（秒）
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

