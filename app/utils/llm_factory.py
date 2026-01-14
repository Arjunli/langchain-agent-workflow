"""LLM 工厂类，支持多种 LLM 提供商"""
from typing import Optional
from langchain_core.language_models import BaseChatModel
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None
) -> BaseChatModel:
    """
    创建 LLM 实例
    
    Args:
        model: 模型名称
        temperature: 温度参数
        provider: LLM 提供商（目前仅支持 "openai"）
    
    Returns:
        LLM 实例
    """
    provider = provider or settings.llm_provider
    
    if provider != "openai":
        logger.warning(f"不支持的 LLM 提供商: {provider}，使用 OpenAI")
        provider = "openai"
    
    if not settings.openai_api_key:
        raise ValueError(
            "OpenAI API key 未配置。请在 .env 文件中设置 OPENAI_API_KEY，"
            "或设置环境变量 OPENAI_API_KEY"
        )
    
    model = model or settings.openai_model
    temperature = temperature if temperature is not None else settings.openai_temperature
    
    return create_openai_llm(model, temperature)


def create_openai_llm(model: str, temperature: float) -> BaseChatModel:
    """创建 OpenAI LLM"""
    try:
        from langchain_openai import ChatOpenAI
        
        if not settings.openai_api_key:
            logger.warning("OpenAI API key 未配置，尝试使用环境变量")
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key
        )
    except Exception as e:
        logger.error(f"创建 OpenAI LLM 失败: {e}")
        raise


