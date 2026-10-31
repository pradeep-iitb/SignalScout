from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ToolResult(BaseModel):
    success: bool
    data: Any
    source: str
    query: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None

class Evidence(BaseModel):
    id: str
    company_id: Optional[str] = None
    claim: str
    source_type: str  # "crustdata_company" | "crustdata_people" | "crustdata_jobs" | "web" | "financial_filing"
    source_name: str
    source_url: Optional[str] = None
    source_reference: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    evidence_text: str
    confidence: float = 1.0  # 0.0 to 1.0

class Signal(BaseModel):
    id: str
    company_id: str
    type: str  # e.g., "headcount_growth", "technical_founder", "enterprise_traction", "job_openings", "funding_velocity"
    description: str
    value: Optional[str] = None
    direction: Literal["positive", "negative", "neutral"]
    strength: float = 0.8  # 0.0 to 1.0
    evidence_ids: List[str] = Field(default_factory=list)

class PersonProfile(BaseModel):
    person_id: str
    name: str
    title: str
    company_id: str
    linkedin_url: Optional[str] = None
    education: List[Dict[str, str]] = Field(default_factory=list)  # [{"school": "IIT Bombay", "degree": "B.Tech", "field": "CSE"}]
    prior_companies: List[Dict[str, str]] = Field(default_factory=list)  # [{"company": "Google", "role": "Staff Engineer", "years": "4"}]
    technical_score: float = 0.0  # 0 to 100
    domain_relevance: float = 0.0  # 0 to 100
    experience_years: int = 0
    verified: bool = False
    evidence_ids: List[str] = Field(default_factory=list)

class CompanyProfile(BaseModel):
    company_id: str
    name: str
    domain: str
    legal_name: Optional[str] = None
    founded_year: Optional[int] = None
    headquarter: str = "Unknown"
    description: str = ""
    stage: str = "Seed"
    total_funding: Optional[str] = None
    last_funding_round: Optional[str] = None
    employee_count: int = 0
    employee_growth_6m: Optional[float] = None
    employee_growth_1y: Optional[float] = None
    web_traffic_monthly: Optional[int] = None
    web_traffic_growth_pct: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    enriched: bool = False
    aliases: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Hypothesis(BaseModel):
    id: str
    company_id: str
    statement: str
    rationale: str
    confidence: float  # 0.0 to 1.0
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradictory_evidence_ids: List[str] = Field(default_factory=list)
    status: Literal["untested", "verified", "challenged", "refuted"] = "untested"
    falsification_criteria: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ScoreComponent(BaseModel):
    score: float
    weight: float
    weighted_score: float
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)

class CandidateScore(BaseModel):
    overall_score: float  # 0 to 100
    confidence: float     # 0 to 100
    thesis_fit: ScoreComponent
    founder_quality: ScoreComponent
    growth_signals: ScoreComponent
    market_fit: ScoreComponent
    momentum: ScoreComponent
    evidence_quality: ScoreComponent
    risk_penalty: ScoreComponent

class InvestigationTask(BaseModel):
    id: str
    company_id: str
    target_type: Literal["founder", "growth", "enterprise_traction", "contradiction", "web_validation"]
    priority_score: float  # Expected Info Gain * Investment Relevance * Uncertainty
    reason: str
    missing_info: str
    suggested_tool: str
    status: Literal["pending", "in_progress", "completed", "skipped"] = "pending"

class AgentAction(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().strftime("%H:%M:%S"))
    node: str
    action: str
    reason: str
    tool: Optional[str] = None
    result: Optional[str] = None
    company_id: Optional[str] = None
    duration_ms: Optional[int] = None

class InvestmentMemo(BaseModel):
    company_id: str
    company_name: str
    stage: str
    location: str
    industry: str
    executive_summary: str
    investment_thesis: str
    why_now: str
    founders_dossier: str
    company_positioning: str
    momentum_analysis: str
    positive_signals: List[str]
    risks: List[str]
    contradictions: List[str]
    what_would_change_our_mind: List[str]
    confidence_score: float
    recommendation: Literal["INVESTIGATE FURTHER", "WATCH", "PASS"]
    cited_evidence_ids: List[str]

class ThesisCriteria(BaseModel):
    raw_prompt: str
    geography: List[str] = Field(default_factory=lambda: ["India"])
    stage: List[str] = Field(default_factory=lambda: ["seed", "series-a"])
    industries: List[str] = Field(default_factory=list)
    business_model: List[str] = Field(default_factory=lambda: ["B2B"])
    preferred_signals: List[str] = Field(default_factory=list)
    negative_signals: List[str] = Field(default_factory=list)
    investment_size: Optional[float] = None
    currency: str = "USD"
    key_evaluation_questions: List[str] = Field(default_factory=list)

class InvestigationRecord(BaseModel):
    id: str
    user_thesis: str
    thesis_criteria: Optional[ThesisCriteria] = None
    search_plan: Optional[Dict[str, Any]] = None
    status: Literal["created", "running", "completed", "failed"] = "created"
    current_node: str = "start"
    iteration: int = 0
    max_iterations: int = 3
    stats: Dict[str, int] = Field(default_factory=lambda: {
        "discovered": 0,
        "resolved": 0,
        "investigated": 0,
        "hypotheses_tested": 0,
        "contradictions_found": 0,
        "shortlisted": 0
    })
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None
