# Build: Autonomous Investment Sourcing Agent

Build a production-quality hackathon prototype called **SignalScout**: an autonomous investment sourcing and research agent for venture funds.

The system should NOT be a chatbot that answers questions about startups.

It should behave like an autonomous junior investment team:

> Investment thesis → discover opportunity universe → identify entities → investigate companies → investigate founders → discover signals → form hypotheses → verify/challenge hypotheses → rank opportunities → produce an investment pipeline and evidence-backed memos.

The core differentiator is **agentic investigation**. The agent must decide what to investigate next based on what it discovers.

---

# 1. PRIMARY USER EXPERIENCE

The user lands on a professional investment research dashboard.

Primary action:

### "Start New Investment Hunt"

The user enters a natural-language thesis, for example:

> Find early-stage Indian B2B SaaS companies building AI infrastructure. Prefer companies with strong technical founders, early enterprise traction, and recent hiring momentum. We can invest up to $5M.

The system should NOT require the user to manually specify:

- company names
- search queries
- founders
- filters
- data sources
- investigation steps

The agent should derive these itself.

After submission, show an active investigation interface.

---

# 2. CORE AGENTIC WORKFLOW

Implement the following LangGraph workflow:

```text
                         USER THESIS
                              │
                              ▼
                    ┌──────────────────┐
                    │ THESIS ANALYZER  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ SEARCH STRATEGY  │
                    │    PLANNER       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ COMPANY DISCOVERY │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ ENTITY RESOLUTION│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ INITIAL ENRICHMENT│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ SIGNAL DISCOVERY │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ CANDIDATE SCORING│
                    └────────┬─────────┘
                             │
                             ▼
                 ┌─────────────────────────┐
                 │ DEEP INVESTIGATION LOOP │
                 └────────────┬────────────┘
                              │
                   ┌──────────┴──────────┐
                   │                     │
              Need more data?        Sufficient
                   │                     │
                   ▼                     ▼
             MORE RESEARCH          HYPOTHESIS
                   │                     │
                   └──────────┐          ▼
                              │    ┌──────────────┐
                              └───►│ VERIFICATION │
                                   └──────┬───────┘
                                          │
                                   ┌──────┴──────┐
                                   │             │
                              Contradiction   Verified
                                   │             │
                                   ▼             ▼
                              Investigate     FINAL SCORE
                                   │             │
                                   └─────────────┤
                                                 ▼
                                       ┌──────────────────┐
                                       │ RANK OPPORTUNITIES│
                                       └────────┬─────────┘
                                                │
                                                ▼
                                       ┌──────────────────┐
                                       │ INVESTMENT MEMOS │
                                       └────────┬─────────┘
                                                │
                                                ▼
                                         FINAL PIPELINE
```

The graph must contain actual branching and loops.

Do NOT implement this as a linear sequence of LLM calls.

---

# 3. TECH STACK

Use:

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui only where useful
- Recharts for simple charts
- Lucide icons

## Backend

- Python
- FastAPI

## Agent

- LangGraph
- LangChain only where genuinely useful
- Pydantic for structured state/models

## LLM

Make the model provider configurable through environment variables.

Create a clean abstraction:

```text
LLM_PROVIDER
LLM_MODEL
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

Do not hardcode a provider throughout the codebase.

## Data

For the hackathon MVP:

- PostgreSQL optional
- Prefer simple in-memory/session state initially
- Persist completed investigations if easy

Do NOT introduce:

- Neo4j
- Redis
- vector database
- complex RAG infrastructure

unless genuinely required.

The investment agent is primarily a structured investigation system, not a semantic-document-retrieval product.

---

# 4. CRUSTDATA INTEGRATION

Crustdata is a CORE dependency, not an optional enrichment.

The application must use Crustdata's canonical people/company data.

Support Crustdata through a dedicated service layer:

```text
backend/
  services/
    crustdata/
      client.py
      companies.py
      people.py
      jobs.py
      web.py
```

Use environment variables:

```env
CRUSTDATA_API_KEY=
CRUSTDATA_API_VERSION=2025-11-01
```

Use:

```http
authorization: Bearer YOUR_API_KEY
x-api-version: 2025-11-01
```

Never expose the API key to the frontend.

Create a `CrustDataClient` abstraction so the agent never directly constructs raw HTTP requests inside graph nodes.

---

# 5. CRUSTDATA TOOLS

Expose Crustdata capabilities as agent tools.

At minimum implement abstractions for:

```text
company_search
company_identify
company_enrich

person_search
person_enrich

job_search

web_search
web_fetch
```

Also create a placeholder interface for watcher functionality so monitoring can be added later.

Each tool should return structured data.

Example:

```python
class ToolResult(BaseModel):
    success: bool
    data: dict
    source: str
    query: str
    timestamp: str
    error: str | None
```

Never return unstructured giant strings when structured data is available.

---

# 6. IMPORTANT: AGENT MUST DECIDE TOOL USAGE

Do NOT make a fixed pipeline such as:

```text
company_search
→ company_enrich
→ person_search
→ web_search
```

Instead, create a reasoning node that decides what information is missing.

Example:

```text
Agent discovers:
Company has strong headcount growth
but founder background is unclear.

Next action:
Person Search → Person Enrich
```

Another example:

```text
Agent discovers:
Company claims enterprise traction
but no independent evidence exists.

Next action:
Web Search → Web Fetch
```

The next tool call should depend on the current state.

---

# 7. LANGGRAPH STATE

Create a strongly typed state.

Suggested structure:

```python
class InvestmentState(TypedDict):

    # User input
    user_thesis: str

    # Parsed investment thesis
    thesis: dict

    # Search strategy
    search_plan: dict

    # Candidate universe
    candidate_companies: list[dict]

    # Current candidate
    current_company: dict | None

    # Company information
    company_profiles: dict

    # People
    founders: dict
    executives: dict

    # Signals
    signals: list[dict]

    # Claims discovered during research
    claims: list[dict]

    # Evidence supporting claims
    evidence: list[dict]

    # Contradictions
    contradictions: list[dict]

    # Hypotheses
    hypotheses: list[dict]

    # Investigation tasks
    investigation_queue: list[dict]

    # Scores
    candidate_scores: dict

    # Verification
    verification_results: dict

    # Final ranked companies
    ranked_candidates: list[dict]

    # Final investment memos
    investment_memos: list[dict]

    # Agent execution metadata
    actions: list[dict]
    iteration: int
    max_iterations: int
```

State should be the source of truth for the entire investigation.

---

# 8. THESIS ANALYZER

Create a node:

```text
analyze_thesis
```

Input:

```text
user's natural-language investment thesis
```

Output structured criteria:

```json
{
  "geography": ["India"],
  "stage": ["pre-seed", "seed", "series-a"],
  "industries": ["B2B SaaS", "AI infrastructure"],
  "business_model": ["B2B"],
  "preferred_signals": [
    "enterprise traction",
    "technical founders",
    "hiring momentum"
  ],
  "negative_signals": [
    "stagnant hiring",
    "unclear founders"
  ],
  "investment_size": 5000000
}
```

Do not force this exact schema if the user's thesis requires something else.

The agent should dynamically derive the investment criteria.

---

# 9. SEARCH STRATEGY PLANNER

Create a planning node.

It should determine:

- what types of companies to search
- what keywords/categories to use
- geography
- company stage
- company size
- relevant people
- relevant signals
- how many initial candidates to discover
- what evidence is required to evaluate the thesis

Example:

```text
THESIS:
Indian AI infrastructure startups

PLAN:

1. Search companies matching AI infrastructure
2. Filter for India
3. Resolve canonical identities
4. Enrich promising companies
5. Find founders
6. Analyze founder background
7. Search hiring signals
8. Search enterprise/customer signals
9. Investigate top candidates
```

The plan should be adaptive.

---

# 10. COMPANY DISCOVERY

The agent should discover companies rather than receiving them.

Use:

```text
company_search
company_identify
```

Generate an initial candidate universe.

Deduplicate entities using canonical company identity.

Store:

```text
company_id
name
domain
industry
location
stage
employees
description
```

Do not hallucinate missing values.

---

# 11. ENTITY RESOLUTION

Create a dedicated node:

```text
resolve_entities
```

Purpose:

- remove duplicate companies
- resolve aliases
- distinguish similarly named companies
- associate people with canonical companies

Every company should have one canonical internal identity.

---

# 12. COMPANY ENRICHMENT

For promising candidates call:

```text
company_enrich
```

Do not enrich every possible company blindly.

The agent should first filter candidates and then spend deeper investigation effort on promising ones.

This demonstrates intelligent tool usage.

---

# 13. FOUNDER / EXECUTIVE INVESTIGATION

For promising companies:

```text
person_search
→ person_enrich
```

Investigate:

- founders
- CEO
- CTO
- relevant leadership

The agent should determine which people matter based on the thesis.

For example:

A deep-tech thesis should investigate technical founder history more heavily.

A fintech thesis should investigate financial-sector experience.

---

# 14. SIGNAL ENGINE

Create a normalized signal model:

```python
class Signal(BaseModel):
    type: str
    description: str
    value: str | None
    direction: Literal["positive", "negative", "neutral"]
    strength: float
    evidence_ids: list[str]
```

Possible signals:

```text
Hiring acceleration
Hiring slowdown
Founder experience
Founder-company history
Executive movement
Funding
Company growth
Employee growth
Industry fit
Geographic fit
Enterprise focus
Technology signals
Competitive signals
Recent activity
```

Do not hardcode that every company must have every signal.

---

# 15. HYPOTHESIS ENGINE

This is one of the most important parts.

After gathering evidence, the agent should form hypotheses.

Example:

```text
Hypothesis:
"Company X is entering a rapid enterprise expansion phase."

Evidence:
+ 30% employee growth
+ enterprise hiring
+ new sales leadership

Confidence:
0.76
```

Then the agent should ask:

```text
What evidence would disprove this?
```

This creates a second investigation path.

---

# 16. CONTRADICTION / VERIFICATION LOOP

Implement:

```text
verify_hypothesis
```

For every important investment claim:

```text
Claim
 ↓
Supporting evidence
 ↓
Contradictory evidence
 ↓
Source quality
 ↓
Recency
 ↓
Confidence
```

Example:

```text
Claim:
"Company is rapidly growing."

Evidence A:
Headcount +35%

Evidence B:
Recent hiring activity

Contradiction:
Company recently lost a major executive

Result:
Growth confidence reduced
```

The agent should be allowed to revisit the company.

Graph:

```text
VERIFY
  │
  ├── VERIFIED ─────────────→ SCORE
  │
  └── CONTRADICTION
             ↓
       INVESTIGATE
             ↓
          VERIFY
```

Limit the loop to a configurable number of iterations.

---

# 17. CANDIDATE SCORING

Do NOT simply ask an LLM:

> "Give this startup a score out of 100."

Create an explicit scoring model.

Example:

```text
Thesis Fit             25%
Founder Quality        20%
Growth Signals         15%
Market/Industry Fit    15%
Momentum               10%
Evidence Quality       10%
Risk                   -5%
```

The weights should be configurable based on the user's thesis.

Every score must have evidence.

Example:

```json
{
  "thesis_fit": {
    "score": 91,
    "reason": "...",
    "evidence_ids": ["ev_12", "ev_19"]
  }
}
```

---

# 18. INVESTIGATION PRIORITY

The agent should decide where to spend investigation effort.

Use a concept like:

```text
investigation_value =
    expected_information_gain
    × investment_relevance
    × uncertainty
```

This means:

If a company already has strong evidence, don't waste calls.

If one unanswered question could radically change the investment decision, investigate it.

Example:

```text
Company A:
High score
but founder history uncertain

→ investigate founder

Company B:
Low thesis fit

→ stop investigation
```

This is a major part of making the system genuinely agentic.

---

# 19. RANKING

After all candidates have sufficient evidence:

```text
rank_candidates
```

Return:

```text
Rank
Company
Overall score
Thesis fit
Founder score
Momentum
Risk
Confidence
Key evidence
Key concern
```

Example:

```text
1. Company A — 88
2. Company B — 83
3. Company C — 79
4. Company D — 72
5. Company E — 68
```

---

# 20. INVESTMENT MEMO GENERATION

Generate a detailed memo only for the top 3–5 companies.

Structure:

```text
INVESTMENT MEMO

Company
Stage
Location
Industry

INVESTMENT THESIS
Why this company fits the fund thesis.

WHY NOW
What changed recently.

FOUNDERS
Relevant background and evidence.

COMPANY
Business and positioning.

MOMENTUM
Hiring / growth / funding / other signals.

POSITIVE SIGNALS
Evidence-backed.

RISKS
Evidence-backed.

CONTRADICTIONS
Evidence that challenges the thesis.

WHAT WOULD CHANGE OUR MIND
Specific future evidence.

CONFIDENCE
0–100%

RECOMMENDATION
INVESTIGATE FURTHER / WATCH / PASS

EVIDENCE
Every major claim linked to its source.
```

Never present unsupported claims as facts.

---

# 21. EVIDENCE MODEL

Create a first-class evidence object:

```python
class Evidence(BaseModel):
    id: str
    claim: str
    source_type: str
    source_name: str
    source_url: str | None
    source_reference: str | None
    retrieved_at: str
    evidence_text: str
    confidence: float
```

Every major claim should reference evidence IDs.

The UI must allow:

```text
Claim → Evidence → Source
```

This is essential because the hackathon evaluation emphasizes data integrity and verifiable reasoning.

---

# 22. AGENT ACTION LOG

Every agent action should be recorded.

Example:

```json
{
  "timestamp": "...",
  "node": "founder_investigation",
  "action": "person_search",
  "reason": "Founder background is currently insufficient to evaluate technical-founder criterion",
  "tool": "crustdata_person_search",
  "result": "3 candidates found"
}
```

This creates an excellent demo feature:

### "Agent Trace"

The user can see:

```text
10:42:03
Analyzed thesis

10:42:05
Discovered 87 companies

10:42:11
Resolved 64 canonical entities

10:42:16
Filtered to 18 candidates

10:42:21
Investigating Company A

10:42:25
Founder evidence insufficient

10:42:26
Searching founder background

10:42:31
Contradictory evidence detected

10:42:34
Investigating contradiction

10:42:41
Hypothesis verified

10:42:43
Company A score updated: 84 → 89
```

This should be a major part of the UI.

---

# 23. FRONTEND

Build a polished investment-research dashboard.

Avoid generic AI-dashboard design.

No:

- excessive gradients
- huge hero graphics
- meaningless badges
- emoji
- excessive cards
- fake metrics
- unnecessary animations

Use a serious institutional / investment-research aesthetic.

Suggested layout:

```text
┌─────────────────────────────────────────────────────────┐
│ SIGNALSCOUT                            New Investment Hunt│
├───────────────┬─────────────────────────────────────────┤
│               │                                         │
│ INVESTIGATION │          ACTIVE INVESTIGATION            │
│               │                                         │
│ Thesis        │  Discovery → Research → Verify → Rank  │
│ Candidates    │                                         │
│ Signals       │  ┌───────────────────────────────────┐  │
│ Evidence      │  │ Current Agent Activity            │  │
│               │  │                                   │  │
│               │  │ Investigating Company X...        │  │
│               │  │ Searching founder evidence...     │  │
│               │  └───────────────────────────────────┘  │
│               │                                         │
└───────────────┴─────────────────────────────────────────┘
```

---

# 24. MAIN RESULTS SCREEN

After completion:

```text
Investment Hunt
────────────────────────────────────

THESIS
Indian AI infrastructure startups...

87 companies discovered
18 investigated
5 shortlisted

────────────────────────────────────

RANKED OPPORTUNITIES

01  Company A                     89
    Strong founder + hiring momentum
    Confidence: 91%

02  Company B                     86
    Strong thesis fit
    Confidence: 84%

03  Company C                     81
    Excellent founder
    Growth evidence weaker
    Confidence: 78%
```

Clicking a company opens its investment memo.

---

# 25. COMPANY DETAIL VIEW

Use:

```text
Company Header

Score: 89
Confidence: 91%

Why this company?
[agent-generated concise explanation]

Signals
────────────────
+ Hiring momentum
+ Founder experience
+ Industry fit
- Limited independent traction evidence

Founder
────────────────
Person profile + evidence

Investigation
────────────────
Timeline of agent actions

Evidence
────────────────
Claim → Source

Contradictions
────────────────
Any conflicting evidence

Recommendation
────────────────
INVESTIGATE FURTHER
```

---

# 26. AGENT GRAPH VIEW

Provide a simple investigation visualization.

Not a generic graph database UI.

Show:

```text
Investment Thesis
      ↓
Company
 ┌────┼─────┐
 ↓    ↓     ↓
Founder Hiring Funding
 ↓
Evidence
 ↓
Hypothesis
 ↓
Verification
```

This should explain the reasoning process.

---

# 27. API ARCHITECTURE

Frontend:

```text
POST /api/investigations
GET  /api/investigations/{id}
GET  /api/investigations/{id}/events
GET  /api/investigations/{id}/candidates
GET  /api/candidates/{id}
GET  /api/candidates/{id}/evidence
```

Backend:

```text
FastAPI
   │
   ├── Investigation API
   │
   ├── LangGraph runtime
   │
   ├── Crustdata service
   │
   ├── Evidence service
   │
   └── Persistence
```

---

# 28. REAL-TIME AGENT TRACE

Use Server-Sent Events or WebSocket if practical.

The frontend should receive events such as:

```json
{
  "type": "agent_action",
  "node": "company_discovery",
  "message": "Searching for AI infrastructure companies in India"
}
```

If realtime implementation becomes a time sink, use polling.

Do not sacrifice the core agent for realtime infrastructure.

---

# 29. ERROR HANDLING

The system must gracefully handle:

- Crustdata API failure
- no companies found
- ambiguous company identity
- missing founder data
- missing enrichment data
- web search failure
- contradictory evidence
- LLM malformed output
- rate limits
- investigation timeout

Never fabricate missing information.

Display:

```text
Data unavailable
```

rather than inventing a value.

---

# 30. OBSERVABILITY

Create a simple developer/debug panel showing:

```text
Node
Tool
Input
Output
Latency
Status
Evidence generated
```

This is useful during the hackathon demo and debugging.

---

# 31. PROJECT STRUCTURE

Use this structure:

```text
signalscout/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
│
├── backend/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── investigations.py
│   │   └── candidates.py
│   │
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes/
│   │   │   ├── thesis.py
│   │   │   ├── planning.py
│   │   │   ├── discovery.py
│   │   │   ├── enrichment.py
│   │   │   ├── investigation.py
│   │   │   ├── verification.py
│   │   │   ├── scoring.py
│   │   │   └── reporting.py
│   │   └── prompts/
│   │
│   ├── tools/
│   │   ├── crustdata/
│   │   └── web/
│   │
│   ├── models/
│   ├── services/
│   └── config/
│
├── .env.example
├── README.md
└── docker-compose.yml
```

Keep frontend and backend independently runnable.

---

# 32. ENVIRONMENT VARIABLES

Create `.env.example`:

```env
LLM_PROVIDER=
LLM_MODEL=

OPENAI_API_KEY=
ANTHROPIC_API_KEY=

CRUSTDATA_API_KEY=
CRUSTDATA_API_VERSION=2025-11-01

DATABASE_URL=

WEB_SEARCH_API_KEY=
```

Never commit `.env`.

---

# 33. DEMO MODE

Create a deterministic demo mode so the entire application can be demonstrated reliably.

Example thesis:

> Find early-stage Indian B2B AI infrastructure startups with strong technical founders and recent growth signals.

Demo should produce:

```text
87 discovered
18 investigated
5 shortlisted
```

But clearly label generated/demo values if they are mocked.

Do not fake live Crustdata responses and present them as real.

The real mode must use the actual Crustdata API.

---

# 34. MOST IMPORTANT PRODUCT PRINCIPLE

Do not build:

```text
Chatbot + Crustdata
```

Build:

```text
Investment Objective
        ↓
Autonomous Investigation
        ↓
Dynamic Tool Selection
        ↓
Evidence Collection
        ↓
Hypothesis Formation
        ↓
Contradiction Search
        ↓
Further Investigation
        ↓
Scoring
        ↓
Decision
        ↓
Investment Pipeline
```

The system should be able to answer:

> "Why did you investigate this company?"

> "Why did you investigate this founder?"

> "Why did you reject this company?"

> "What evidence supports this score?"

> "What evidence contradicts your thesis?"

> "What would change your recommendation?"

The agent trace should make these answers visible.

---

# 35. BUILD PRIORITY

Implement in this order:

### P0 — MUST WORK

1. Next.js frontend
2. FastAPI backend
3. LangGraph state
4. Crustdata client
5. Company search
6. Company identify/enrich
7. Person search/enrich
8. Dynamic investigation loop
9. Evidence model
10. Verification
11. Candidate scoring
12. Final investment pipeline

### P1

13. Agent trace
14. Company detail page
15. Investment memo
16. Contradiction visualization
17. Real-time progress

### P2

18. Persistence
19. Watchers
20. Advanced charts
21. Backtesting
22. Historical/as-of-date evaluation

Do not spend hackathon time polishing P2 features before P0 works.

---

# 36. FINAL SUCCESS CRITERIA

The application is complete when a user can enter a completely new investment thesis and the system can:

```text
1. Understand the thesis
2. Create an investigation strategy
3. Discover companies
4. Resolve company identities
5. Enrich companies
6. Find and investigate relevant people
7. Discover investment signals
8. Decide what requires further investigation
9. Form investment hypotheses
10. Search for contradictory evidence
11. Re-investigate when necessary
12. Score candidates
13. Rank opportunities
14. Generate evidence-backed investment memos
15. Explain every major decision
```

The entire workflow must execute without the user manually directing individual research steps.

The final product should feel like:

> **"Give me an investment thesis and I will build the investment pipeline for you."**

not:

> **"Ask me questions about startups."**

Start by scaffolding the repository, frontend, backend, LangGraph state/graph, Crustdata service abstraction, environment configuration, and a minimal end-to-end vertical slice. Then progressively implement the remaining nodes and UI.