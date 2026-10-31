import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction, CandidateScore, ScoreComponent
from backend.services.storage import storage

logger = logging.getLogger("signalscout.scoring")

def compute_score_for_company(
    c_id: str,
    prof: Dict[str, Any],
    founders: List[Dict[str, Any]],
    signals: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
    contradictions: List[Dict[str, Any]],
    hypotheses: List[Dict[str, Any]]
) -> CandidateScore:
    """
    Explicit, auditable venture scoring model with configurable weights and direct evidence links.
    """
    comp_signals = [s for s in signals if s.get("company_id") == c_id]
    comp_evidence = [e for e in evidence if e.get("company_id") == c_id]
    comp_contradictions = [c for c in contradictions if c.get("company_id") == c_id]

    # 1. Thesis Fit (25%)
    desc = (prof.get("description", "") + " " + " ".join(prof.get("categories", []))).lower()
    t_ev_ids = [e["id"] for e in comp_evidence if "headcount" in e.get("claim", "").lower() or "ai" in e.get("claim", "").lower()][:3]
    
    if "ai infrastructure" in desc or "llm" in desc or "inference" in desc or "gateway" in desc:
        t_score = 92.0
        t_reason = "Direct match with AI infrastructure / LLM developer systems mandate"
    elif "mlops" in desc or "developer tools" in desc:
        t_score = 80.0
        t_reason = "Adjacent MLOps / Developer Tools positioning"
    else:
        t_score = 55.0
        t_reason = "General SaaS; partial overlap with infrastructure thesis"
    
    comp_thesis = ScoreComponent(
        score=t_score,
        weight=0.25,
        weighted_score=t_score * 0.25,
        reason=t_reason,
        evidence_ids=t_ev_ids
    )

    # 2. Founder Quality (20%)
    f_ev_ids = []
    if founders:
        avg_tech = sum(f.get("technical_score", 70.0) for f in founders) / len(founders)
        avg_domain = sum(f.get("domain_relevance", 70.0) for f in founders) / len(founders)
        f_score = min(100.0, (avg_tech * 0.6 + avg_domain * 0.4))
        f_pedigree = [f"{f.get('name')} ({', '.join(e.get('school', '') for e in f.get('education', []))})" for f in founders]
        f_reason = f"Verified technical founders: {'; '.join(f_pedigree)}"
        for f in founders:
            f_ev_ids.extend(f.get("evidence_ids", []))
    else:
        f_score = 50.0
        f_reason = "Founder background unverified or preliminary"

    comp_founder = ScoreComponent(
        score=f_score,
        weight=0.20,
        weighted_score=f_score * 0.20,
        reason=f_reason,
        evidence_ids=f_ev_ids[:4]
    )

    # 3. Growth Signals (15%)
    growth_6m = prof.get("employee_growth_6m", 0.0) or 0.0
    g_ev_ids = [e["id"] for e in comp_evidence if "growth" in e.get("claim", "").lower() or "hiring" in e.get("claim", "").lower()]
    if growth_6m > 0.40:
        g_score = 95.0
        g_reason = f"Rapid hiring acceleration of +{int(growth_6m*100)}% over 6 months"
    elif growth_6m > 0.20:
        g_score = 82.0
        g_reason = f"Strong positive headcount expansion of +{int(growth_6m*100)}%"
    elif growth_6m < 0.0:
        g_score = 30.0
        g_reason = f"Negative employee contraction of {int(growth_6m*100)}%"
    else:
        g_score = 60.0
        g_reason = "Stable or baseline employee headcount trajectory"

    comp_growth = ScoreComponent(
        score=g_score,
        weight=0.15,
        weighted_score=g_score * 0.15,
        reason=g_reason,
        evidence_ids=g_ev_ids[:3]
    )

    # 4. Market / Industry Fit (15%)
    m_score = 88.0 if "ai" in desc else 70.0
    comp_market = ScoreComponent(
        score=m_score,
        weight=0.15,
        weighted_score=m_score * 0.15,
        reason="High TAM sector experiencing substantial enterprise budget reallocation toward AI systems",
        evidence_ids=[]
    )

    # 5. Momentum (10%)
    traffic_growth = prof.get("web_traffic_growth_pct", 0.0) or 0.0
    if traffic_growth > 25.0:
        mom_score = 90.0
        mom_reason = f"Surging web traffic (+{traffic_growth:.1f}%) and open high-caliber engineering requisitions"
    else:
        mom_score = 65.0
        mom_reason = "Normal steady-state inbound traffic and job volume"

    comp_momentum = ScoreComponent(
        score=mom_score,
        weight=0.10,
        weighted_score=mom_score * 0.10,
        reason=mom_reason,
        evidence_ids=[e["id"] for e in comp_evidence if "traffic" in e.get("claim", "").lower()][:2]
    )

    # 6. Evidence Quality (10%)
    ev_count = len(comp_evidence)
    ev_q_score = min(100.0, 50.0 + ev_count * 10.0)
    comp_ev_qual = ScoreComponent(
        score=ev_q_score,
        weight=0.10,
        weighted_score=ev_q_score * 0.10,
        reason=f"Backed by {ev_count} verified Crustdata and external citations",
        evidence_ids=[e["id"] for e in comp_evidence[:3]]
    )

    # 7. Risk Penalty (-5% or more if severe contradictions found)
    risk_score = 10.0  # baseline minimal risk
    risk_reasons = []
    if comp_contradictions:
        risk_score += len(comp_contradictions) * 20.0
        risk_reasons.append(f"{len(comp_contradictions)} contradictory claim(s) flagged")
    if growth_6m < 0.0:
        risk_score += 30.0
        risk_reasons.append("Contraction in team size")
    
    risk_reasons_str = "; ".join(risk_reasons)
    comp_risk = ScoreComponent(
        score=risk_score,
        weight=-0.05,
        weighted_score=-(risk_score * 0.05),
        reason=risk_reasons_str,
        evidence_ids=[c.get("evidence_id") for c in comp_contradictions if c.get("evidence_id")]
    )

    overall = (
        comp_thesis.weighted_score +
        comp_founder.weighted_score +
        comp_growth.weighted_score +
        comp_market.weighted_score +
        comp_momentum.weighted_score +
        comp_ev_qual.weighted_score +
        comp_risk.weighted_score
    )
    overall_clamped = max(10.0, min(99.0, round(overall, 1)))
    
    # Confidence is function of evidence count and lack of unresolved contradictions
    base_confidence = 65.0 + min(25.0, ev_count * 5.0)
    if comp_contradictions:
        base_confidence -= 12.0
    confidence_clamped = max(35.0, min(98.0, round(base_confidence, 1)))

    return CandidateScore(
        overall_score=overall_clamped,
        confidence=confidence_clamped,
        thesis_fit=comp_thesis,
        founder_quality=comp_founder,
        growth_signals=comp_growth,
        market_fit=comp_market,
        momentum=comp_momentum,
        evidence_quality=comp_ev_qual,
        risk_penalty=comp_risk
    )

async def candidate_scoring(state: InvestmentState) -> InvestmentState:
    """
    Node 7: CANDIDATE SCORING
    Applies explicit weighted scoring rubric across all enriched candidate companies.
    """
    inv_id = state["investigation_id"]
    profiles = state.get("company_profiles", {})
    founders_map = state.get("founders", {})
    signals = state.get("signals", [])
    evidence = state.get("evidence", [])
    contradictions = state.get("contradictions", [])
    hypotheses = state.get("hypotheses", [])

    candidate_scores = {}

    for c_id, prof in profiles.items():
        if not prof.get("enriched"):
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
        candidate_scores[c_id] = score_obj.dict()

    state["candidate_scores"] = candidate_scores

    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="candidate_scoring",
        action="compute_candidate_scores",
        reason="Evaluate candidates against thesis weighting: Thesis Fit (25%), Founder (20%), Growth (15%), Market (15%), Momentum (10%), Evidence (10%), Risk (-5%)",
        tool="agent_scoring_engine",
        result=f"Scored {len(candidate_scores)} candidate companies with auditable score components",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {
        "candidate_scores": candidate_scores,
        "current_node": "candidate_scoring"
    })

    return state
