import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.models.entities import InvestigationRecord, Evidence, AgentAction

class InvestigationStorage:
    def __init__(self):
        self._investigations: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._evidence: Dict[str, Dict[str, Any]] = {}
        self._listeners: Dict[str, List[asyncio.Queue]] = {}

    def create(self, investigation_id: str, thesis: str) -> Dict[str, Any]:
        record = {
            "id": investigation_id,
            "user_thesis": thesis,
            "status": "created",
            "current_node": "start",
            "iteration": 0,
            "max_iterations": 3,
            "stats": {
                "discovered": 0,
                "resolved": 0,
                "investigated": 0,
                "hypotheses_tested": 0,
                "contradictions_found": 0,
                "shortlisted": 0
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "thesis_criteria": None,
            "search_plan": None,
            "ranked_candidates": [],
            "investment_memos": [],
            "actions": [],
            "error": None
        }
        self._investigations[investigation_id] = record
        self._events[investigation_id] = []
        self._listeners[investigation_id] = []
        return record

    def reset(self):
        """Clear session data."""
        self._investigations.clear()
        self._events.clear()
        self._candidates.clear()
        self._evidence.clear()
        self._listeners.clear()

    def get(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        return self._investigations.get(investigation_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return sorted(list(self._investigations.values()), key=lambda x: x.get("created_at", ""), reverse=True)

    def update(self, investigation_id: str, updates: Dict[str, Any]):
        if investigation_id in self._investigations:
            self._investigations[investigation_id].update(updates)
            self._investigations[investigation_id]["updated_at"] = datetime.utcnow().isoformat()

    def add_action(self, investigation_id: str, action: Dict[str, Any]):
        if investigation_id in self._investigations:
            self._investigations[investigation_id]["actions"].append(action)
        self.emit_event(investigation_id, {
            "type": "agent_action",
            "action": action
        })

    def emit_event(self, investigation_id: str, event: Dict[str, Any]):
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().strftime("%H:%M:%S")
        if investigation_id in self._events:
            self._events[investigation_id].append(event)
        
        # Broadcast to active SSE listeners
        if investigation_id in self._listeners:
            for q in list(self._listeners[investigation_id]):
                try:
                    q.put_nowait(event)
                except Exception:
                    pass

    def get_events(self, investigation_id: str) -> List[Dict[str, Any]]:
        return self._events.get(investigation_id, [])

    def register_listener(self, investigation_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if investigation_id not in self._listeners:
            self._listeners[investigation_id] = []
        self._listeners[investigation_id].append(q)
        return q

    def unregister_listener(self, investigation_id: str, q: asyncio.Queue):
        if investigation_id in self._listeners and q in self._listeners[investigation_id]:
            self._listeners[investigation_id].remove(q)

    def save_candidate_profile(self, candidate: Dict[str, Any]):
        c_id = candidate.get("company_id")
        if c_id:
            self._candidates[c_id] = candidate

    def get_candidate_profile(self, company_id: str) -> Optional[Dict[str, Any]]:
        return self._candidates.get(company_id)

    def save_evidence(self, ev: Dict[str, Any]):
        ev_id = ev.get("id")
        if ev_id:
            self._evidence[ev_id] = ev

    def get_evidence(self, ev_id: str) -> Optional[Dict[str, Any]]:
        return self._evidence.get(ev_id)

    def get_evidence_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        return [ev for ev in self._evidence.values() if ev.get("company_id") == company_id]

storage = InvestigationStorage()
