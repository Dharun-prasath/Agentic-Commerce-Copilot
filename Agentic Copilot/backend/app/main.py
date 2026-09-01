from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import RequestLoggingMiddleware
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agentic Commerce Copilot...")
    # Check/create tables
    from app.core.database import engine
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start Queue Manager
    from app.services.orchestrator.queue_manager import QueueManager
    QueueManager.get_instance().start()
    
    yield
    # Shutdown
    logger.info("Shutting down Agentic Commerce Copilot...")

app = FastAPI(
    title="Agentic Commerce Copilot API",
    description="API for the Agentic Commerce Copilot platform",
    version="1.0.0",
    lifespan=lifespan
)

# Allow CORS for Electron app and React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability
app.add_middleware(RequestLoggingMiddleware)

from app.api.v1.endpoints import (
    events, whatsapp, voice, telegram, dashboard, agents, system, intent,
    orchestrator, product_intelligence, commerce_internal
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(events.router, prefix="/api/v1/integration/events", tags=["events"])
app.include_router(intent.router, prefix="/api/v1/intent", tags=["intent"])
app.include_router(whatsapp.router, prefix="/api/v1/integrations/whatsapp", tags=["whatsapp"])
app.include_router(telegram.router, prefix="/api/v1/integrations/telegram", tags=["telegram"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

# Internal APIs for Multi-Agent Orchestration
app.include_router(orchestrator.router, prefix="/api/v1/internal/orchestrator", tags=["internal-orchestrator"])
app.include_router(product_intelligence.router, prefix="/api/v1/internal/product-intelligence", tags=["internal-pi"])
app.include_router(commerce_internal.router, prefix="/api/v1/internal/commerce", tags=["internal-commerce"])
