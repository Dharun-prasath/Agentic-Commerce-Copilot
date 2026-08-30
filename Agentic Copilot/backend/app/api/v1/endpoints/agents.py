from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid
import datetime

from app.core.database import get_db
from app.models.models import AgentConfig

router = APIRouter()

class AgentConfigUpdate(BaseModel):
    is_active: bool | None = None
    model_name: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    max_output_tokens: int | None = None
    system_prompt: str | None = None
    context_memory_size: int | None = None
    capabilities: Dict[str, Any] | None = None
    fallback_behavior: str | None = None
    output_formatting: str | None = None
    processing_timeout_ms: int | None = None

class AgentConfigResponse(BaseModel):
    id: str
    agent_id: str
    is_active: bool
    model_name: str
    temperature: float
    top_p: float
    top_k: int
    max_output_tokens: int
    system_prompt: str
    context_memory_size: int
    capabilities: Dict[str, Any]
    fallback_behavior: str
    output_formatting: str
    processing_timeout_ms: int
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    class Config:
        from_attributes = True

@router.get("/config", response_model=List[AgentConfigResponse])
async def get_all_agent_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentConfig))
    configs = result.scalars().all()
    
    # If no configs exist, initialize defaults
    if not configs:
        default_agents = ["intent", "sales", "product", "commerce"]
        new_configs = []
        for agent_id in default_agents:
            config = AgentConfig(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                system_prompt=f"You are the {agent_id} agent."
            )
            db.add(config)
            new_configs.append(config)
        await db.commit()
        for config in new_configs:
            await db.refresh(config)
        configs = new_configs
        
    return configs

@router.put("/config/{agent_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    agent_id: str,
    update_data: AgentConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Config for agent '{agent_id}' not found.")
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(config, key, value)
        
    await db.commit()
    await db.refresh(config)
    
    return config
