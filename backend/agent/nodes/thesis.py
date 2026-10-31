import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import ThesisCriteria, AgentAction
from backend.services.storage import storage
from backend.services.llm import llm_service

logger = logging.getLogger("signalscout.thesis")

async def analyze_thesis(state: InvestmentState) -> InvestmentState:
    """
    Node 1: THESIS ANALYZER
    Translates raw user thesis into structured investment criteria and evaluation questions.
    """
    user_thesis = state["user_thesis"]
    inv_id = state["investigation_id"]

    parsed = await llm_service.generate_json(f"""Analyze this venture investment thesis and return JSON only:
{user_thesis}
Schema: geography (array), stage (array), industries (array), business_model (array),
preferred_signals (array), negative_signals (array), investment_size (number or null),
currency (string), key_evaluation_questions (array of strings).""")

    criteria = ThesisCriteria(
        raw_prompt=user_thesis,
        geography=parsed.get("geography", []),
        stage=parsed.get("stage", []),
        industries=parsed.get("industries", []),
        business_model=parsed.get("business_model", []),
        preferred_signals=parsed.get("preferred_signals", []),
        negative_signals=parsed.get("negative_signals", []),
        investment_size=parsed.get("investment_size"),
        currency=parsed.get("currency", "USD"),
        key_evaluation_questions=parsed.get("key_evaluation_questions", [])
    )

    state["thesis"] = criteria.dict()
    
    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="thesis_analyzer",
        action="parse_thesis",
        reason="Deconstruct natural language thesis into quantifiable venture investment criteria",
        tool="gemini_thesis_parser",
        result=f"Extracted {len(criteria.industries)} target sectors in {', '.join(criteria.geography)} at {', '.join(criteria.stage)} stage",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {"thesis_criteria": criteria.dict(), "current_node": "thesis_analyzer"})

    return state
