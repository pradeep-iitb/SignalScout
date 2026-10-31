import logging
import asyncio
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from backend.models.state import InvestmentState
from backend.agent.nodes.thesis import analyze_thesis
from backend.agent.nodes.planning import search_strategy_planner
from backend.agent.nodes.discovery import company_discovery
from backend.agent.nodes.entity_resolution import resolve_entities
from backend.agent.nodes.enrichment import initial_enrichment
from backend.agent.nodes.signals import signal_discovery
from backend.agent.nodes.scoring import candidate_scoring
from backend.agent.nodes.deep_investigation import deep_investigation_loop
from backend.agent.nodes.verification import verify_hypothesis
from backend.agent.nodes.contradiction_investigation import investigate_contradiction
from backend.agent.nodes.ranking import rank_opportunities
from backend.agent.nodes.reporting import generate_investment_memos
from backend.services.storage import storage

logger = logging.getLogger("signalscout.graph")

def traced_node(name, handler):
    async def run(state):
        logger.info("[STEP START] %s | investigation=%s", name, state.get("investigation_id"))
        print(f"[STEP START] {name}", flush=True)
        try:
            result = await handler(state)
            logger.info("[STEP END] %s | candidates=%d evidence=%d actions=%d", name, len(result.get("candidate_companies", [])), len(result.get("evidence", [])), len(result.get("actions", [])))
            print(f"[STEP END] {name} | candidates={len(result.get('candidate_companies', []))} evidence={len(result.get('evidence', []))} actions={len(result.get('actions', []))}", flush=True)
            return result
        except Exception as error:
            logger.exception("[STEP ERROR] %s | %s", name, error)
            print(f"[STEP ERROR] {name} | {error}", flush=True)
            raise
    return run

def should_continue_investigation(state: InvestmentState) -> Literal["more_research", "verify"]:
    """
    Branching condition 1: Does the agent have critical unanswered questions
    and remaining iteration budget?
    """
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 2)
    queue = state.get("investigation_queue", [])

    high_priority_pending = [t for t in queue if t.get("priority_score", 0) > 0.40 and t.get("status") == "pending"]

    if iteration < max_iter and len(high_priority_pending) > 0:
        logger.info(f"Branching: Need more research (iteration {iteration}/{max_iter}, {len(high_priority_pending)} high-priority tasks)")
        return "more_research"
    
    logger.info("Branching: Research sufficient -> Proceeding to Hypothesis Verification")
    return "verify"

def should_investigate_contradiction(state: InvestmentState) -> Literal["investigate_contradiction", "rank"]:
    """
    Branching condition 2: Was a significant contradiction flagged that requires
    targeted secondary investigation?
    """
    contradictions = state.get("contradictions", [])
    recheck_count = state.get("contradiction_recheck_count", 0)

    uninvestigated = [c for c in contradictions if not c.get("investigated") and c.get("severity") == "high"]

    if uninvestigated and recheck_count < 1:
        logger.info(f"Branching: Contradiction flagged ({len(uninvestigated)} uninvestigated) -> Secondary Contradiction Audit")
        return "investigate_contradiction"

    logger.info("Branching: Verification complete -> Proceeding to Ranking")
    return "rank"

def build_investment_graph():
    """
    Constructs the full autonomous investment sourcing and research LangGraph
    with actual conditional branching, loops, and adversarial verification.
    """
    workflow = StateGraph(InvestmentState)

    # Add all workflow nodes
    workflow.add_node("thesis_analyzer", traced_node("thesis_analyzer", analyze_thesis))
    workflow.add_node("search_strategy_planner", traced_node("search_strategy_planner", search_strategy_planner))
    workflow.add_node("company_discovery", traced_node("company_discovery", company_discovery))
    workflow.add_node("entity_resolution", traced_node("entity_resolution", resolve_entities))
    workflow.add_node("initial_enrichment", traced_node("initial_enrichment", initial_enrichment))
    workflow.add_node("signal_discovery", traced_node("signal_discovery", signal_discovery))
    workflow.add_node("candidate_scoring", traced_node("candidate_scoring", candidate_scoring))
    workflow.add_node("deep_investigation_loop", traced_node("deep_investigation_loop", deep_investigation_loop))
    workflow.add_node("hypothesis_verification", traced_node("hypothesis_verification", verify_hypothesis))
    workflow.add_node("investigate_contradiction", traced_node("investigate_contradiction", investigate_contradiction))
    workflow.add_node("rank_opportunities", traced_node("rank_opportunities", rank_opportunities))
    workflow.add_node("investment_memos", traced_node("investment_memos", generate_investment_memos))

    # Define linear preliminary pipeline
    workflow.add_edge(START, "thesis_analyzer")
    workflow.add_edge("thesis_analyzer", "search_strategy_planner")
    workflow.add_edge("search_strategy_planner", "company_discovery")
    workflow.add_edge("company_discovery", "entity_resolution")
    workflow.add_edge("entity_resolution", "initial_enrichment")
    workflow.add_edge("initial_enrichment", "signal_discovery")
    workflow.add_edge("signal_discovery", "candidate_scoring")
    workflow.add_edge("candidate_scoring", "deep_investigation_loop")

    # Branch 1: Deep Investigation Loop
    workflow.add_conditional_edges(
        "deep_investigation_loop",
        should_continue_investigation,
        {
            "more_research": "deep_investigation_loop",
            "verify": "hypothesis_verification"
        }
    )

    # Branch 2: Contradiction / Verification Loop
    workflow.add_conditional_edges(
        "hypothesis_verification",
        should_investigate_contradiction,
        {
            "investigate_contradiction": "investigate_contradiction",
            "rank": "rank_opportunities"
        }
    )

    # Contradiction loop returns back to verification to recalculate confidence
    workflow.add_edge("investigate_contradiction", "hypothesis_verification")

    # Final pipeline stages
    workflow.add_edge("rank_opportunities", "investment_memos")
    workflow.add_edge("investment_memos", END)

    return workflow.compile()

# Compile singleton graph
investment_agent_graph = build_investment_graph()

async def run_investigation(investigation_id: str, user_thesis: str) -> Dict[str, Any]:
    """
    Executes the autonomous investment sourcing graph asynchronously in background.
    """
    initial_state: InvestmentState = {
        "investigation_id": investigation_id,
        "user_thesis": user_thesis,
        "thesis": {},
        "search_plan": {},
        "candidate_companies": [],
        "current_company": None,
        "company_profiles": {},
        "founders": {},
        "executives": {},
        "signals": [],
        "claims": [],
        "evidence": [],
        "contradictions": [],
        "hypotheses": [],
        "investigation_queue": [],
        "candidate_scores": {},
        "verification_results": {},
        "ranked_candidates": [],
        "investment_memos": [],
        "actions": [],
        "iteration": 0,
        "max_iterations": 2,
        "error": None
    }

    storage.update(investigation_id, {"status": "running"})

    try:
        final_state = await investment_agent_graph.ainvoke(initial_state)
        storage.update(investigation_id, {
            "status": "completed",
            "thesis_criteria": final_state.get("thesis"),
            "search_plan": final_state.get("search_plan"),
            "ranked_candidates": final_state.get("ranked_candidates", []),
            "investment_memos": final_state.get("investment_memos", []),
            "actions": final_state.get("actions", []),
            "current_node": "completed"
        })
        storage.emit_event(investigation_id, {
            "type": "investigation_completed",
            "ranked_count": len(final_state.get("ranked_candidates", [])),
            "memos_count": len(final_state.get("investment_memos", []))
        })
        return final_state
    except Exception as e:
        error_text = str(e) or type(e).__name__
        logger.error(f"Investigation execution failed: {error_text}", exc_info=True)
        storage.update(investigation_id, {
            "status": "failed",
            "error": error_text
        })
        storage.emit_event(investigation_id, {
            "type": "investigation_failed",
            "error": error_text
        })
        raise e
