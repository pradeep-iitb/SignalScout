# SignalScout

SignalScout is an agentic investment-sourcing workspace. It turns a natural-language investment thesis into a structured research plan, discovers and enriches companies, evaluates signals, verifies hypotheses, ranks opportunities, and generates investment memos.

## What is included

- Next.js frontend dashboard
- FastAPI backend
- LangGraph investigation workflow
- Gemini or Grok for thesis analysis and search planning
- Crustdata for live company, people, jobs, and web research
- Explicit local mock-data mode for demos and development

## Project status

This is a functional hackathon MVP. The end-to-end agent flow is wired and the frontend/backend integration is working. Investigations are currently stored in memory, so restarting the backend clears the workspace. Authentication, durable job execution, persistent storage, and production hardening are not yet implemented.

## Requirements

- Python 3.11+ recommended
- Node.js 20+ recommended
- API credentials for the providers used in live investigations

## Setup

### Backend

From the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example configuration to the project root:

```powershell
Copy-Item .env.example .env
```

Fill in the keys in `.env`. Never commit `.env`.

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`; documentation is at `http://127.0.0.1:8000/docs`.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If the backend uses another URL, set:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Environment configuration

`.env.example` contains the complete configuration template.

### LLM provider

The provider is selected in `.env`, not in the UI:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.8-flash
GEMINI_API_KEY=your_gemini_key
```

For Grok:

```env
LLM_PROVIDER=grok
XAI_API_KEY=your_xai_key
XAI_MODEL=grok-3-mini
XAI_BASE_URL=https://api.x.ai/v1
```

`GROK_API_KEY` is also accepted for compatibility with existing local configurations.

### Crustdata

```env
CRUSTDATA_API_KEY=your_crustdata_key
CRUSTDATA_API_VERSION=2025-11-01
```

### Data modes

The UI data toggle controls the workspace:

- **Live Crustdata** uses the configured Crustdata API and reports configuration/upstream errors explicitly.
- **Mock data** uses local fixture records instead of making Crustdata requests and seeds a populated dashboard.

The default is:

```env
USE_MOCK_DATA=false
```

## Investigation flow

Submitting **New investment hunt** sends the thesis to `POST /api/investigations`. The backend creates an investigation and runs this LangGraph workflow in a background task:

```text
Thesis analyzer
  -> Search strategy planner
  -> Company discovery
  -> Entity resolution
  -> Initial enrichment
  -> Signal discovery
  -> Candidate scoring
  -> Deep investigation loop
  -> Hypothesis verification
  -> Contradiction investigation, when required
  -> Opportunity ranking
  -> Investment memo generation
```

Gemini or Grok is used by the thesis analyzer and search strategy planner. Crustdata, or the local mock provider, supplies company, people, jobs, and web research data. The LLM plans and interprets the research; it does not replace the data provider.

Progress is streamed to the frontend over Server-Sent Events. The backend prints step, LLM, and data-provider tracing in the terminal.

## API endpoints

- `GET /api/health` - backend, data-mode, and LLM readiness
- `GET /api/system/status` - workspace counts and configuration status
- `POST /api/system/workspace?mode=fresh` - clear workspace and use live mode
- `POST /api/system/workspace?mode=mock` - clear workspace and seed mock mode
- `POST /api/investigations` - create an investigation
- `GET /api/investigations` - list investigations
- `GET /api/investigations/{id}` - inspect an investigation
- `GET /api/investigations/{id}/events` - stream progress over SSE
- `GET /api/investigations/{id}/candidates` - retrieve ranked candidates

## Validation

```powershell
cd frontend
npm run build
```

```powershell
cd backend
.\venv\Scripts\python.exe -m compileall -q app main.py agent api config services
```

## Security notes

- Never commit `.env` or API keys.
- Rotate credentials if exposed in logs, screenshots, commits, or chat.
- Restrict CORS and add authentication before public deployment.
- Live mode should be tested with valid provider credentials and the current Crustdata API contract.
