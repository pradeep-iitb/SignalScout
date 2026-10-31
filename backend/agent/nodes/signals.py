import logging
from datetime import datetime
from backend.models.state import InvestmentState
from backend.models.entities import AgentAction, Signal, Evidence
from backend.services.storage import storage

logger = logging.getLogger("signalscout.signals")

async def signal_discovery(state: InvestmentState) -> InvestmentState:
    """
    Node 6: SIGNAL DISCOVERY
    Discovers quantitative and qualitative signals across enriched candidate companies.
    """
    inv_id = state["investigation_id"]
    profiles = state.get("company_profiles", {})
    evidence_list = state.get("evidence", [])
    signals = list(state.get("signals", []))

    discovered_signals_count = 0

    for c_id, prof in profiles.items():
        if not prof.get("enriched"):
            continue

        growth_6m = prof.get("employee_growth_6m")
        growth_1y = prof.get("employee_growth_1y")
        traffic_growth = prof.get("web_traffic_growth_pct")
        name = prof.get("name")
        domain = prof.get("domain")

        # 1. Headcount Growth Signal
        if growth_6m is not None:
            sig_id = f"sig_growth_{c_id}"
            ev_id = f"ev_growth_{c_id}"
            
            if growth_6m >= 0.25:
                direction = "positive"
                desc = f"Rapid 6-month headcount acceleration of +{int(growth_6m * 100)}%"
                strength = min(1.0, 0.6 + growth_6m)
            elif growth_6m <= 0.0:
                direction = "negative"
                desc = f"Stagnant or declining headcount contraction of {int(growth_6m * 100)}% over 6 months"
                strength = 0.85
            else:
                direction = "neutral"
                desc = f"Moderate organic headcount increase of +{int(growth_6m * 100)}% over 6 months"
                strength = 0.6

            ev = Evidence(
                id=ev_id,
                company_id=c_id,
                claim=desc,
                source_type="crustdata_company",
                source_name="Crustdata Canonical Employee Telemetry",
                source_url=f"https://api.crustdata.com/company/enrich?domain={domain}",
                evidence_text=f"Historical verified monthly employee headcount delta: 6-month rate = {growth_6m:.2%}, 1-year rate = {growth_1y or 0:.2%}.",
                confidence=0.94
            )
            evidence_list.append(ev.dict())
            storage.save_evidence(ev.dict())

            sig = Signal(
                id=sig_id,
                company_id=c_id,
                type="Hiring acceleration" if direction == "positive" else ("Hiring slowdown" if direction == "negative" else "Company growth"),
                description=desc,
                value=f"+{int(growth_6m * 100)}%" if growth_6m >= 0 else f"{int(growth_6m * 100)}%",
                direction=direction,
                strength=strength,
                evidence_ids=[ev_id]
            )
            signals.append(sig.dict())
            discovered_signals_count += 1

        # 2. Web Traffic Momentum Signal
        if traffic_growth is not None and traffic_growth > 20.0:
            sig_id = f"sig_traffic_{c_id}"
            ev_id = f"ev_traffic_{c_id}"
            ev = Evidence(
                id=ev_id,
                company_id=c_id,
                claim=f"High organic developer interest: +{traffic_growth:.1f}% monthly web traffic surge",
                source_type="crustdata_company",
                source_name="Crustdata Web Traffic Analytics",
                source_url=f"https://api.crustdata.com/company/enrich?domain={domain}",
                evidence_text=f"Estimated monthly web visitors: {prof.get('web_traffic_monthly', 0):,}, monthly growth trajectory: {traffic_growth:.1f}%.",
                confidence=0.88
            )
            evidence_list.append(ev.dict())
            storage.save_evidence(ev.dict())

            sig = Signal(
                id=sig_id,
                company_id=c_id,
                type="Technology signals",
                description=f"Developer adoption surge (+{traffic_growth:.1f}% monthly traffic)",
                value=f"+{traffic_growth:.1f}%",
                direction="positive",
                strength=0.75,
                evidence_ids=[ev_id]
            )
            signals.append(sig.dict())
            discovered_signals_count += 1

        # 3. Industry / Thesis Fit Signal
        categories = prof.get("categories", [])
        if any("ai infrastructure" in cat.lower() or "llm" in cat.lower() for cat in categories):
            sig_id = f"sig_ind_{c_id}"
            sig = Signal(
                id=sig_id,
                company_id=c_id,
                type="Industry fit",
                description="Core AI infrastructure alignment (LLM Ops, Inference optimization, systems compute)",
                value=", ".join(categories[:3]),
                direction="positive",
                strength=0.90,
                evidence_ids=[]
            )
            signals.append(sig.dict())
            discovered_signals_count += 1

    state["signals"] = signals
    state["evidence"] = evidence_list

    action = AgentAction(
        timestamp=datetime.utcnow().strftime("%H:%M:%S"),
        node="signal_discovery",
        action="discover_signals",
        reason="Evaluate headcount deltas, developer web adoption, and sector alignment across candidate profiles",
        tool="crustdata_signal_engine",
        result=f"Extracted {discovered_signals_count} verifiable quantitative and qualitative signals",
        company_id=None
    )
    state["actions"].append(action.dict())
    storage.add_action(inv_id, action.dict())
    storage.update(inv_id, {
        "signals_count": len(signals),
        "current_node": "signal_discovery"
    })

    return state
