import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction
from backend.services.storage import storage
from backend.services.llm import llm_service
from backend.tools.crustdata import tool_company_search, tool_company_identify

logger = logging.getLogger("signalscout.discovery")

async def company_discovery(state: InvestmentState) -> InvestmentState:
    """
    Node 3: COMPANY DISCOVERY
    Autonomous market discovery driven by AI reasoning and live Crustdata verification:
    1. LLM analyzes user thesis and identifies actual operating startups matching the thesis
    2. Cross-references and verifies candidates against Crustdata's live entity resolution graph
    3. Queries Crustdata company screener for matching sector entities
    """
    inv_id = state["investigation_id"]
    plan = state.get("search_plan", {})
    queries = plan.get("search_queries", ["AI Infrastructure India"])
    geo = plan.get("geography_filter", ["India"])
    stages = plan.get("stages_filter", ["Seed", "Series A"])
    thesis = state.get("thesis", {})

    discovered_universe = []
    seen_domains = set()

    # STRATEGY 1: Autonomous AI Entity Discovery based on Investment Thesis
    action_llm = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="company_discovery",
        action="autonomous_market_scan",
        reason="Deploy LLM intelligence to identify active startups strictly aligned with investment thesis parameters",
        tool="gemini_market_discovery",
        result="Conducting autonomous market discovery",
        company_id=None
    )
    state["actions"].append(action_llm.dict())
    storage.add_action(inv_id, action_llm.dict())

    try:
        industries = thesis.get("industries", ["AI Infrastructure", "B2B SaaS"])
        geography = thesis.get("geography", ["India"])
        stage_str = ", ".join(thesis.get("stage", ["Seed", "Series A"]))
        ind_str = ", ".join(industries)
        geo_str = ", ".join(geography)

        llm_prompt = f"""You are a senior partner at a venture capital fund conducting an investment hunt.
Analyze this investment mandate and identify 12 to 16 real operating startups matching all criteria:

MANDATE:
Thesis: {thesis.get('raw_prompt', '')}
Target Sectors: {ind_str}
Geography: {geo_str}
Target Stages: {stage_str}

Provide a JSON object with a "companies" array. Each item must represent a real company:
- "name": Official company name (e.g. "Sarvam AI", "Portkey", "Simplismart", "Composio", "TrueFoundry")
- "domain": Primary web domain (e.g. "sarvam.ai", "portkey.ai", "simplismart.io", "composio.dev")
- "headquarter": City and country
- "stage": Funding stage (e.g. "Seed", "Series A")
- "employee_count": Estimated current team size
- "employee_growth_6m": Estimated 6-month headcount growth rate as decimal (e.g. 0.42 for +42%)
- "total_funding": Estimated capital raised (e.g. "$4.5M")
- "description": Concrete technical product description and core differentiator
- "categories": Array of relevant industry tags"""

        llm_result = await llm_service.generate_json(llm_prompt)
        llm_companies = llm_result.get("companies", [])

        for c in llm_companies:
            dom = c.get("domain", "").lower().strip()
            if dom and dom not in seen_domains:
                seen_domains.add(dom)
                if "company_id" not in c:
                    c["company_id"] = f"comp_{dom.split('.')[0]}"
                discovered_universe.append(c)

        action_llm_result = AgentAction(
            timestamp=datetime.utcnow().strftime("%H:%M:%S"),
            node="company_discovery",
            action="candidates_identified",
            reason=f"Identified {len(discovered_universe)} active startups matching investment mandate",
            tool="gemini_market_discovery",
            result=f"Discovered {len(discovered_universe)} candidate companies matching criteria",
            company_id=None
        )
        state["actions"].append(action_llm_result.dict())
        storage.add_action(inv_id, action_llm_result.dict())

    except Exception as e:
        logger.warning(f"AI company discovery warning: {e}")

    # STRATEGY 2: Live Crustdata Entity Cross-Verification
    verified_count = 0
    for c in discovered_universe[:10]:
        domain = c.get("domain", "")
        if domain:
            try:
                ident_res = await tool_company_identify(domain)
                if ident_res.success and ident_res.data.get("entity"):
                    entity = ident_res.data.get("entity", {})
                    if entity.get("canonical_name"):
                        c["name"] = entity.get("canonical_name", c.get("name"))
                        c["crustdata_verified"] = True
                        verified_count += 1
            except Exception:
                pass

    if verified_count > 0:
        action_verify = AgentAction(
            timestamp=datetime.utcnow().strftime("%H:%M:%S"),
            node="company_discovery",
            action="crustdata_verification",
            reason=f"Cross-referenced discovered companies against Crustdata live identity endpoint",
            tool="crustdata_company_identify",
            result=f"Verified {verified_count} entities live in Crustdata graph",
            company_id=None
        )
        state["actions"].append(action_verify.dict())
        storage.add_action(inv_id, action_verify.dict())

    # STRATEGY 3: Live Crustdata Screener Search (if accessible on account tier)
    for q in queries[:2]:
        tool_res = await tool_company_search(query=q, geography=geo, stage=stages, limit=20)
        if tool_res.success:
            companies = tool_res.data.get("companies", [])
            for c in companies:
                dom = c.get("domain", "").lower()
                if dom and dom not in seen_domains:
                    seen_domains.add(dom)
                    discovered_universe.append(c)

    state["candidate_companies"] = discovered_universe

    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="company_discovery",
        action="universe_assembled",
        reason="Synthesize verified multi-source candidates into active opportunity pool",
        tool="signalscout_discovery_engine",
        result=f"Universe assembled: {len(discovered_universe)} candidate startups ready for enrichment",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {
        "candidate_companies_count": len(discovered_universe),
        "current_node": "company_discovery",
        "stats": {
            "discovered": len(discovered_universe),
            "resolved": 0,
            "investigated": 0,
            "hypotheses_tested": 0,
            "contradictions_found": 0,
            "shortlisted": 0
        }
    })

    return state
