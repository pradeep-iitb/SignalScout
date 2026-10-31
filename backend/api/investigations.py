import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.services.storage import storage
from backend.agent.graph import run_investigation
from backend.config.settings import settings

logger = logging.getLogger("signalscout.api")

router = APIRouter(prefix="/api/investigations", tags=["investigations"])

class StartInvestigationRequest(BaseModel):
    thesis: str
    max_iterations: Optional[int] = 2

@router.post("")
async def create_investigation(req: StartInvestigationRequest, background_tasks: BackgroundTasks):
    if not req.thesis.strip():
        raise HTTPException(status_code=400, detail="Investment thesis cannot be empty")
    
    inv_id = f"inv_{uuid.uuid4().hex[:10]}"
    storage.create(inv_id, req.thesis.strip())

    # Launch autonomous agent in background task
    asyncio.create_task(run_investigation(inv_id, req.thesis.strip()))

    return {
        "investigation_id": inv_id,
        "status": "running",
        "message": "SignalScout autonomous investment hunt initialized",
        "thesis": req.thesis.strip()
    }

@router.get("")
async def list_investigations():
    return storage.list_all()

@router.get("/{investigation_id}")
async def get_investigation(investigation_id: str):
    record = storage.get(investigation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return record

@router.get("/{investigation_id}/events")
async def stream_investigation_events(investigation_id: str):
    record = storage.get(investigation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")

    async def event_generator():
        # First send any existing backlog of events
        backlog = storage.get_events(investigation_id)
        for ev in backlog:
            yield {
                "event": ev.get("type", "agent_action"),
                "data": ev
            }

        if record.get("status") in ["completed", "failed"]:
            yield {
                "event": "done",
                "data": {"status": record.get("status")}
            }
            return

        # Listen for real-time live events
        queue = storage.register_listener(investigation_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield {
                        "event": event.get("type", "agent_action"),
                        "data": event
                    }
                    if event.get("type") in ["investigation_completed", "investigation_failed"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield {
                        "event": "ping",
                        "data": {"timestamp": "heartbeat"}
                    }
        finally:
            storage.unregister_listener(investigation_id, queue)

    return EventSourceResponse(event_generator())

@router.get("/{investigation_id}/candidates")
async def get_investigation_candidates(investigation_id: str):
    record = storage.get(investigation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return record.get("ranked_candidates", [])
