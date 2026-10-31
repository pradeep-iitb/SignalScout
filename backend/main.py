import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.api import investigations_router, candidates_router
from backend.services.storage import storage
from backend.agent.graph import run_investigation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("signalscout")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SignalScout Autonomous Investment Sourcing Agent Backend...")
    logger.info("Crustdata API: %s", "Configured" if settings.CRUSTDATA_API_KEY else "NOT CONFIGURED")

    yield
    logger.info("Shutting down SignalScout Backend...")

app = FastAPI(
    title="SignalScout - Autonomous Investment Sourcing Agent",
    description="Agentic investment sourcing, deep company/founder diligence, and evidence-backed memo generation",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations_router)
app.include_router(candidates_router)

@app.get("/")
async def api_root():
    return {
        "service": "SignalScout API",
        "status": "running",
        "frontend": "http://localhost:3000",
        "docs": "/docs",
        "health": "/api/health",
        "investigations": "/api/investigations",
    }

@app.post("/api/system/workspace")
async def reset_workspace():
    storage.reset()
    return {"status": "reset", "message": "Workspace cleared."}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SignalScout Autonomous Investment Sourcing Agent",
        "engine": "LangGraph + Gemini + Crustdata Live",
        "crustdata_configured": bool(settings.CRUSTDATA_API_KEY),
        "crustdata_version": settings.CRUSTDATA_API_VERSION,
        "llm_provider": settings.LLM_PROVIDER.lower(),
        "llm_configured": bool(settings.GEMINI_API_KEY if settings.LLM_PROVIDER.lower() == "gemini" else (settings.XAI_API_KEY or settings.GROK_API_KEY)),
    }

@app.get("/api/system/status")
async def system_status():
    all_invs = storage.list_all()
    return {
        "active_investigations": len([i for i in all_invs if i.get("status") == "running"]),
        "completed_investigations": len([i for i in all_invs if i.get("status") == "completed"]),
        "total_investigations": len(all_invs),
        "crustdata_live": bool(settings.CRUSTDATA_API_KEY),
        "llm_provider": settings.LLM_PROVIDER.lower(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
