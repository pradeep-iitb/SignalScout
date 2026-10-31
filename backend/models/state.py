from typing import TypedDict, Optional, List, Dict, Any

class InvestmentState(TypedDict):
    # Investigation ID
    investigation_id: str

    # User input
    user_thesis: str

    # Parsed investment thesis
    thesis: Dict[str, Any]

    # Search strategy
    search_plan: Dict[str, Any]

    # Candidate universe (raw discovered)
    candidate_companies: List[Dict[str, Any]]

    # Current candidate being investigated in loop
    current_company: Optional[Dict[str, Any]]

    # Resolved and enriched company profiles {company_id: profile_dict}
    company_profiles: Dict[str, Dict[str, Any]]

    # People associated with candidates {company_id: [founder_profiles]}
    founders: Dict[str, List[Dict[str, Any]]]
    executives: Dict[str, List[Dict[str, Any]]]

    # Discovered signals [{id, company_id, type, description, direction, strength, evidence_ids}]
    signals: List[Dict[str, Any]]

    # Claims discovered during research [{id, company_id, text, source}]
    claims: List[Dict[str, Any]]

    # Evidence supporting claims [{id, company_id, claim, source_type, source_name, source_url, evidence_text, confidence}]
    evidence: List[Dict[str, Any]]

    # Contradictions [{id, company_id, hypothesis_id, contradiction_text, evidence_id, severity}]
    contradictions: List[Dict[str, Any]]

    # Hypotheses [{id, company_id, statement, rationale, confidence, supporting_evidence_ids, contradictory_evidence_ids, status, falsification_criteria}]
    hypotheses: List[Dict[str, Any]]

    # Dynamic investigation queue [{id, company_id, target_type, priority_score, reason, missing_info, suggested_tool}]
    investigation_queue: List[Dict[str, Any]]

    # Scores {company_id: score_dict}
    candidate_scores: Dict[str, Dict[str, Any]]

    # Verification results {company_id: verification_summary}
    verification_results: Dict[str, Dict[str, Any]]

    # Final ranked companies
    ranked_candidates: List[Dict[str, Any]]

    # Final investment memos
    investment_memos: List[Dict[str, Any]]

    # Agent execution trace / action log
    actions: List[Dict[str, Any]]
    
    # Loop management
    iteration: int
    max_iterations: int
    
    # Execution error if any
    error: Optional[str]
