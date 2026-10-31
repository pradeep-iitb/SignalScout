import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction
from backend.services.storage import storage
from backend.services.llm import llm_service

logger = logging.getLogger("signalscout.planning")

async def search_strategy_planner(state: InvestmentState) -> InvestmentState:
    """
    Node 2: SEARCH STRATEGY PLANNER
    Formulates a targeted discovery and multi-hop investigation strategy based on the parsed thesis.
    """
    thesis = state["thesis"]
    inv_id = state["investigation_id"]

    industries = thesis.get("industries", ["AI Infrastructure", "B2B SaaS"])
    geography = thesis.get("geography", ["India"])
    stages = thesis.get("stage", ["Seed", "Series A"])

    plan_prompt = f"""Create a Crustdata investigation search plan for this thesis criteria:
{thesis}
Return JSON only with search_queries (array of strings), geography_filter (array),
stages_filter (array), primary_signals (array), contradiction_checks (array),
required_people_roles (array), min_employee_count, max_employee_count."""

    try:
        plan = await llm_service.generate_json(plan_prompt)
    except Exception as e:
        logger.warning(f"Planner LLM generation error: {e}. Using deterministic plan.")
        plan = {}

    if not isinstance(plan, dict):
        plan = {}

    search_queries = plan.get("search_queries", [])
    if not search_queries:
        search_queries = [
            f"{ind} {' '.join(geography)}" for ind in industries
        ]
        if "AI Infrastructure" in industries:
            search_queries.extend([
                "LLM inference and observability India",
                "GPU cloud systems India",
                "Developer infrastructure India"
            ])

    plan.update({
        "search_queries": search_queries[:6],
        "geography_filter": plan.get("geography_filter", geography),
        "stages_filter": plan.get("stages_filter", stages),
        "min_employee_count": plan.get("min_employee_count", 3),
        "max_employee_count": plan.get("max_employee_count", 150),
        "target_discovery_pool": 80,
        "shortlist_pool_target": 18,
        "final_pipeline_target": 5,
        "primary_signals": plan.get("primary_signals", [
            "Headcount growth >= 25% over last 6 months",
            "Active engineering and solutions architect requisitions",
            "Technical founder pedigree (IIT/BITS/ex-FAANG)",
            "Enterprise production reference accounts"
        ]),
        "contradiction_checks": plan.get("contradiction_checks", [
            "Executive attrition or departed technical co-founders",
            "Stalled headcount growth (< 5% over 1 year)",
            "Stage mismatch exceeding early-stage venture check size"
        ]),
        "required_people_roles": plan.get("required_people_roles", ["Founder", "Co-Founder", "CEO", "CTO", "Head of AI"])
    })

    state["search_plan"] = plan

    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="search_strategy_planner",
        action="formulate_plan",
        reason="Define query matrix, canonical entity filters, and multi-hop verification requirements",
        tool="agent_planner",
        result=f"Generated {len(plan['search_queries'])} discovery queries with {len(plan.get('contradiction_checks', []))} contradiction checkpoints",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {"search_plan": plan, "current_node": "search_strategy_planner"})

    return state
