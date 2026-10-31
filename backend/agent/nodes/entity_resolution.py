import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction, CompanyProfile
from backend.services.storage import storage
from backend.tools.crustdata import tool_company_identify

logger = logging.getLogger("signalscout.entity_resolution")

async def resolve_entities(state: InvestmentState) -> InvestmentState:
    """
    Node 4: ENTITY RESOLUTION
    Deduplicates candidates, resolves legal aliases, and maps to canonical Crustdata identifiers.
    Optimized for high-speed resolution across large discovered candidate universes.
    """
    inv_id = state["investigation_id"]
    candidates = state.get("candidate_companies", [])

    resolved_map = {}
    resolved_profiles = {}
    aliases_encountered = 0
    seen_domains = set()

    for idx, c in enumerate(candidates):
        domain = c.get("domain", "").lower().strip()
        name = c.get("name", "").strip()

        # Deduplicate identical domains immediately
        if domain in seen_domains:
            aliases_encountered += 1
            continue
        seen_domains.add(domain)

        # For the primary top candidates (first 10), run identify check
        if idx < 10:
            ident_res = await tool_company_identify(domain or name)
            if ident_res.success:
                entity_data = ident_res.data.get("entity", {})
                canonical_id = entity_data.get("company_id") or c.get("company_id")
                canonical_name = entity_data.get("canonical_name") or name
                canonical_domain = entity_data.get("domain") or domain
            else:
                canonical_id = c.get("company_id") or f"crust_comp_{domain.split('.')[0]}"
                canonical_name = name
                canonical_domain = domain
        else:
            canonical_id = c.get("company_id") or f"crust_comp_{domain.split('.')[0]}"
            canonical_name = name
            canonical_domain = domain

        if canonical_id in resolved_map:
            aliases_encountered += 1
            continue

        profile = CompanyProfile(
            company_id=canonical_id,
            name=canonical_name,
            domain=canonical_domain,
            legal_name=c.get("legal_name", canonical_name),
            founded_year=c.get("founded_year"),
            headquarter=c.get("headquarter", "India"),
            description=c.get("description", ""),
            stage=c.get("stage", "Seed"),
            total_funding=c.get("total_funding"),
            last_funding_round=c.get("last_funding_round"),
            employee_count=c.get("employee_count", 10),
            employee_growth_6m=c.get("employee_growth_6m"),
            employee_growth_1y=c.get("employee_growth_1y"),
            web_traffic_monthly=c.get("web_traffic_monthly"),
            web_traffic_growth_pct=c.get("web_traffic_growth_pct"),
            categories=c.get("categories", ["AI Infrastructure"]),
            linkedin_url=c.get("linkedin_url"),
            website_url=c.get("website_url"),
            enriched=False,
            aliases=c.get("aliases", []),
            metadata=c.get("metadata", {})
        )
        resolved_map[canonical_id] = profile.dict()
        resolved_profiles[canonical_id] = profile.dict()

    state["company_profiles"] = resolved_profiles
    state["candidate_companies"] = list(resolved_map.values())

    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="entity_resolution",
        action="resolve_canonical_identities",
        reason="Deduplicate messy domain variants and merge brand aliases into canonical company entities",
        tool="crustdata_company_identify",
        result=f"Resolved {len(candidates)} raw entries into {len(resolved_map)} unique canonical identities ({aliases_encountered} aliases merged)",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {
        "resolved_count": len(resolved_map),
        "current_node": "entity_resolution"
    })

    return state
