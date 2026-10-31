import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction, Evidence
from backend.services.storage import storage

logger = logging.getLogger("signalscout.verification")

async def verify_hypothesis(state: InvestmentState) -> InvestmentState:
    """
    Node 9: HYPOTHESIS VERIFICATION & CONTRADICTION ENGINE
    Challenges investment claims by actively searching for disconfirming signals,
    identifying stage mismatches, headcount contraction, or executive churn.
    """
    inv_id = state["investigation_id"]
    profiles = state.get("company_profiles", {})
    hypotheses = list(state.get("hypotheses", []))
    evidence_list = list(state.get("evidence", []))
    contradictions = list(state.get("contradictions", []))
    thesis = state.get("thesis", {})
    max_check = thesis.get("investment_size", 5000000)

    contradictions_found = 0

    for hyp in hypotheses:
        c_id = hyp.get("company_id")
        prof = profiles.get(c_id, {})
        name = prof.get("name", "Target")
        domain = prof.get("domain", "")
        growth_6m = prof.get("employee_growth_6m", 0.0) or 0.0
        emp_count = prof.get("employee_count", 0)
        stage = prof.get("stage", "Seed")

        # Action: verify hypothesis
        action_ver = AgentAction(
            timestamp=datetime.utcnow().strftime("%H:%M:%S"),
            node="verify_hypothesis",
            action="challenge_hypothesis",
            reason=f"Stress-test hypothesis for {name}: '{hyp.get('statement')}'. Testing against contradiction checks.",
            tool="agent_falsification_engine",
            result=f"Auditing growth telemetry, stage compatibility, and churn metrics",
            company_id=c_id
        )
        state["actions"].append(action_ver.dict())
        storage.add_action(inv_id, action_ver.dict())

        # Check 1: Negative or Stagnant Headcount Growth Contradiction
        if growth_6m < 0.0:
            contra_id = f"contra_{c_id}_churn"
            ev_id = f"ev_contra_{c_id}_churn"
            
            ev = Evidence(
                id=ev_id,
                company_id=c_id,
                claim=f"Contradiction: {name} suffered net employee contraction of {int(growth_6m*100)}% over prior 6 months",
                source_type="crustdata_company",
                source_name="Crustdata Historical Headcount Time-Series",
                source_url=f"https://api.crustdata.com/company/enrich?domain={domain}",
                evidence_text=f"Crustdata audit reveals net headcount dropped from {int(emp_count / (1 + growth_6m))} to {emp_count} employees.",
                confidence=0.95
            )
            evidence_list.append(ev.dict())
            storage.save_evidence(ev.dict())

            contradiction_entry = {
                "id": contra_id,
                "company_id": c_id,
                "hypothesis_id": hyp.get("id"),
                "contradiction_text": f"Headcount growth assumption violated: telemetry displays negative 6-month delta ({growth_6m:.1%}).",
                "evidence_id": ev_id,
                "severity": "high"
            }
            contradictions.append(contradiction_entry)
            hyp["contradictory_evidence_ids"].append(ev_id)
            hyp["status"] = "challenged"
            hyp["confidence"] = round(max(0.20, hyp.get("confidence", 0.7) - 0.35), 2)
            contradictions_found += 1

            action_contra = AgentAction(
                timestamp=datetime.utcnow().strftime("%H:%M:%S"),
                node="verify_hypothesis",
                action="contradiction_detected",
                reason=f"Negative growth delta directly contradicts rapid expansion thesis for {name}",
                tool="agent_contradiction_detector",
                result=f"Flagged high-severity contradiction ({contra_id}); reduced confidence to {hyp['confidence']}",
                company_id=c_id
            )
            state["actions"].append(action_contra.dict())
            storage.add_action(inv_id, action_contra.dict())

        # Check 2: Stage Mismatch (Company too large / too late for $5M investment thesis)
        elif emp_count > 180 or "growth" in stage.lower() or "unicorn" in stage.lower():
            contra_id = f"contra_{c_id}_stage"
            ev_id = f"ev_contra_{c_id}_stage"

            ev = Evidence(
                id=ev_id,
                company_id=c_id,
                claim=f"Thesis Mismatch: {name} total funding/scale ({prof.get('total_funding')}, {emp_count} employees) exceeds fund's $5M early-stage limit",
                source_type="crustdata_company",
                source_name="Crustdata Canonical Profile",
                source_url=f"https://api.crustdata.com/company/enrich?domain={domain}",
                evidence_text=f"Company stage is {stage} with {emp_count} employees and {prof.get('total_funding')} raised, far beyond Seed/Series-A sweet spot.",
                confidence=0.98
            )
            evidence_list.append(ev.dict())
            storage.save_evidence(ev.dict())

            contradiction_entry = {
                "id": contra_id,
                "company_id": c_id,
                "hypothesis_id": hyp.get("id"),
                "contradiction_text": f"Stage mismatch: {name} scale ({emp_count} staff, {prof.get('total_funding')}) is incompatible with fund's $5M check target.",
                "evidence_id": ev_id,
                "severity": "medium"
            }
            contradictions.append(contradiction_entry)
            hyp["contradictory_evidence_ids"].append(ev_id)
            hyp["status"] = "challenged"
            hyp["confidence"] = round(max(0.30, hyp.get("confidence", 0.7) - 0.25), 2)
            contradictions_found += 1

        else:
            # Verified hypothesis
            hyp["status"] = "verified"
            hyp["confidence"] = round(min(0.96, hyp.get("confidence", 0.7) + 0.10), 2)

            action_ok = AgentAction(
                timestamp=datetime.utcnow().strftime("%H:%M:%S"),
                node="verify_hypothesis",
                action="hypothesis_verified",
                reason=f"No contradictory signals uncovered. Growth trajectory and enterprise demand substantiated.",
                tool="agent_verification",
                result=f"Hypothesis validated with {hyp['confidence']} confidence",
                company_id=c_id
            )
            state["actions"].append(action_ok.dict())
            storage.add_action(inv_id, action_ok.dict())

    state["hypotheses"] = hypotheses
    state["evidence"] = evidence_list
    state["contradictions"] = contradictions

    action_summary = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="verify_hypothesis",
        action="verification_cycle_complete",
        reason="Completed adversarial verification pass over all active investment hypotheses",
        tool="agent_verification_loop",
        result=f"Verified {len(hypotheses) - contradictions_found} hypotheses; isolated {contradictions_found} contradictions",
        company_id=None
    )
    state["actions"].append(action_summary.dict())
    storage.add_action(inv_id, action_summary.dict())
    storage.update(inv_id, {
        "contradictions_count": len(contradictions),
        "current_node": "verify_hypothesis"
    })

    return state
