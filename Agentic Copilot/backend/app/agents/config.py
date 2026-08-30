from sqlalchemy.future import select
from app.core.database import async_session_maker
from app.models.models import AgentConfig

async def get_agent_config(agent_id: str) -> dict:
    """Fetch live configuration for the given agent from the database."""
    async with async_session_maker() as db:
        result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
        config = result.scalar_one_or_none()
        if config:
            return {
                "is_active": config.is_active,
                "model_name": config.model_name,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "max_output_tokens": config.max_output_tokens,
                "system_prompt": config.system_prompt,
                "context_memory_size": config.context_memory_size,
                "capabilities": config.capabilities or {},
                "fallback_behavior": config.fallback_behavior,
                "output_formatting": config.output_formatting,
                "processing_timeout_ms": config.processing_timeout_ms
            }
    return {}
