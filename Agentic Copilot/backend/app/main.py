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
    # Add initializations here (DB pools, etc)
    from app.services.intent_intelligence.sweeper import start_sweeper, stop_sweeper
    from app.services.intent_intelligence.queue_worker import start_queue_worker, stop_queue_worker
    
    # Check/create tables
    from app.core.database import engine
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    start_sweeper()
    start_queue_worker()
    yield
    await stop_sweeper()
    await stop_queue_worker()
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

from app.api.v1.endpoints import events, whatsapp, voice, telegram, dashboard, agents, system, intent

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

