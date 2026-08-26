"""
Agentic Commerce — FastAPI Application Entry Point

This is the merchant e-commerce application.
The Agentic Commerce Copilot integrates via clean APIs.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Commerce — E-Commerce API",
    description="""
## Agentic Commerce Merchant API

A production-quality e-commerce API for laptops and electronics.

### Integration
The **Agentic Commerce Copilot** integrates with this API via:
- `/api/v1/products` — Product catalog
- `/api/v1/events` — Customer behaviour events  
- `/api/v1/cart` — Cart management
- `/api/v1/checkout` — Checkout flow
- `/api/v1/payments` — Payment processing

### Authentication
Most endpoints use JWT Bearer authentication.
Cart endpoints support anonymous sessions via `X-Session-Id` header.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "Agentic Commerce API",
        "version": "1.0.0",
        "status": "ok",
        "razorpay_configured": settings.razorpay_configured,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
