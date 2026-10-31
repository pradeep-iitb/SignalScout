from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.models.entities import ToolResult

class WatcherSubscription(BaseModel):
    id: str
    target_type: str  # "company" | "person" | "job"
    target_identifier: str
    event_types: List[str]  # e.g., ["headcount_growth", "executive_departure", "funding_round", "new_role_opened"]
    webhook_url: Optional[str] = None
    created_at: str = datetime.utcnow().isoformat()
    status: str = "active"

async def tool_create_watcher(target_type: str, target_identifier: str, event_types: List[str], webhook_url: Optional[str] = None) -> ToolResult:
    """
    Crustdata Watcher Placeholder Interface.
    Allows registering webhooks when a person, company, or job changes.
    """
    watcher_id = f"watch_{target_type}_{target_identifier.replace('.', '_')}"
    subscription = WatcherSubscription(
        id=watcher_id,
        target_type=target_type,
        target_identifier=target_identifier,
        event_types=event_types,
        webhook_url=webhook_url
    )
    return ToolResult(
        success=True,
        data=subscription.dict(),
        source="crustdata_watcher",
        query=f"create_watcher: {target_type} -> {target_identifier}",
        timestamp=datetime.utcnow().isoformat(),
        error=None
    )
