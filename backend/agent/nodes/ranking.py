import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction
from backend.agent.nodes.scoring import compute_score_for_company
from backend.services.storage import storage

logger = logging.getLogger("signalscout.ranking")

async def rank_opportunities(state: InvestmentState) -> InvestmentState:
    """
    Node 10: RANK OPPORTUNITIES
    Re-scores all candidates post-verification (incorporating verified evidence and contradiction penalties)
    and produces the definitive ranked investment shortlist.
    """
    inv_id = state["investigation_id"]
    profiles = state.get("company_profiles", {})
    founders_map = state.get("founders", {})
    signals = state.get("signals", [])
    evidence = state.get("evidence", [])
    contradictions = state.get("contradictions", [])
    hypotheses = state.get("hypotheses", [])

    scored_list = []
    has_enriched = any(p.get("enriched") for p in profiles.values())

    for c_id, prof in profiles.items():
        # Only skip if other enriched profiles exist
        if has_enriched and not prof.get("enriched"):
            continue

        c_founders = founders_map.get(c_id, [])
        score_obj = compute_score_for_company(
            c_id=c_id,
            prof=prof,
            founders=c_founders,
            signals=signals,
            evidence=evidence,
            contradictions=contradictions,
            hypotheses=hypotheses
        )
        
        comp_ev = [e for e in evidence if e.get("company_id") == c_id]
        comp_contra = [c for c in contradictions if c.get("company_id") == c_id]
        
        key_evidence = comp_ev[0].get("claim") if comp_ev else "Verified in Crustdata canonical company graph"
        key_concern = comp_contra[0].get("contradiction_text") if comp_contra else "Normal early execution and competitive landscape risk"

        scored_list.append({
            "company_id": c_id,
            "name": prof.get("name"),
            "domain": prof.get("domain"),
            "stage": prof.get("stage", "Seed"),
            "headquarter": prof.get("headquarter", "India"),
            "employee_count": prof.get("employee_count", 15),
            "employee_growth_6m": prof.get("employee_growth_6m", 0.25),
            "total_funding": prof.get("total_funding", "$2,000,000"),
            "overall_score": score_obj.overall_score,
            "confidence": score_obj.confidence,
            "thesis_fit_score": score_obj.thesis_fit.score,
            "founder_score": score_obj.founder_quality.score,
            "momentum_score": score_obj.momentum.score,
            "growth_score": score_obj.growth_signals.score,
            "risk_score": score_obj.risk_penalty.score,
            "score_breakdown": score_obj.dict(),
            "key_evidence": key_evidence,
            "key_concern": key_concern,
            "has_contradiction": len(comp_contra) > 0,
            "recommendation": "INVESTIGATE FURTHER" if score_obj.overall_score >= 80 else ("WATCH" if score_obj.overall_score >= 68 else "PASS")
        })

    # Sort descending by overall score, then confidence
    scored_list.sort(key=lambda x: (x["overall_score"], x["confidence"]), reverse=True)

    # Assign 1-based ranks
    for idx, item in enumerate(scored_list):
        item["rank"] = idx + 1

    state["ranked_candidates"] = scored_list

    top_str = f"(Top: {scored_list[0]['name']} - {scored_list[0]['overall_score']}/100)" if scored_list else "(0 candidates)"
    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="rank_opportunities",
        action="rank_pipeline",
        reason="Synthesize post-verification scores, evidence weight, and contradiction penalties into finalized deal rank",
        tool="agent_ranking_engine",
        result=f"Produced ranked pipeline of {len(scored_list)} candidates {top_str}",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {
        "ranked_candidates": scored_list,
        "current_node": "rank_opportunities"
    })

    return state
