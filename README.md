# SalesOps AI

**AI-Powered Lead Qualification & Sales Automation Platform**

SalesOps AI helps sales teams capture, qualify, prioritize, and act on incoming leads. **Phase 4** is a full-stack, portfolio-quality sales operations workspace: a responsive Next.js dashboard backed by FastAPI, explainable scoring, pipeline management, activity history, follow-up tasks, and AI-assisted sales intelligence that works without a paid API.

## Current features

- Create, retrieve, update, and delete leads
- Explainable 0–100 lead scoring with Hot, Warm, and Cold classifications
- Six-stage sales pipeline: New, Qualified, Contacted, Proposal, Won, and Lost
- Automatic and manual lead activity timeline
- Follow-up tasks with priorities, lifecycle states, overdue and upcoming views
- Lead detail view model for a future professional frontend
- Structured qualification summaries, buying signals, risks, and next-best actions
- Personalized follow-up subject and message generation
- Deterministic local intelligence provider requiring no API account
- Optional OpenAI provider with structured-output validation and local fallback
- Search across lead name, company, and need
- Filter by qualification status, pipeline stage, and score range
- Pagination and safe field-based sorting
- Consistent validation and error responses
- PostgreSQL health check and structured application logging
- Alembic-managed database schema
- Automated API and scoring tests
- Responsive executive dashboard with live KPIs and Recharts visualizations
- Lead table, CRM record, pipeline board, task center, and analytics screens
- Professional loading, empty, error, validation, and action states

## Technology stack

- Python 3.12
- FastAPI and Pydantic
- SQLAlchemy 2.x and PostgreSQL 16
- Alembic migrations
- Pytest and FastAPI TestClient
- Docker Compose
- Next.js 16, React 19, and strict TypeScript
- Tailwind CSS 4 and shadcn/ui component conventions
- Recharts and Lucide icons
- Vitest and Testing Library

## Architecture

```text
Browser :3000
    │
    ▼
Next.js App Router + TypeScript
    ├── app/          routes and layouts
    ├── components/   reusable shadcn-style UI
    ├── features/     dashboard, leads, pipeline, tasks, intelligence
    ├── hooks/        remote-data lifecycle
    └── lib/api.ts    centralized API client
    │
    ▼ HTTP / JSON
FastAPI :8001
    ├── api/          routes and HTTP error handling
    ├── services/     scoring, workflow, and intelligence rules
    ├── models/       SQLAlchemy persistence
    └── schemas/      validated public contracts
    │
    ▼
PostgreSQL 16 + Alembic
```

The HTTP layer validates input and coordinates requests. Business rules live in focused service modules. SQLAlchemy models define `Lead → Activities`, `Lead → Tasks`, and `Lead → Latest Intelligence` relationships with database-enforced cascading. Pydantic schemas define every public API and provider response. Tables are created only through Alembic migrations.

### AI provider flow

```text
Lead + Score + Pipeline + Recent Activities + Pending Tasks
                            │
                            ▼
               Sales Intelligence Service
                   ┌────────┴────────┐
                   ▼                 ▼
          Local AI Provider    OpenAI Provider
          deterministic        optional + validated
                   └────────┬────────┘
                            ▼
       Summary + Signals + Risks + Action + Follow-up
                            │
                            ▼
                Latest result persisted
```

## Quick start with Docker

1. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

2. Replace the example password in `.env` and make the password in `DATABASE_URL` match.

3. Build and start PostgreSQL, FastAPI, and Next.js:

   ```bash
   docker compose up --build
   ```

The application is available at `http://localhost:3000`. The API and interactive documentation are at `http://localhost:8001` and `http://localhost:8001/docs`.

Compose applies all pending migrations before starting the API. Existing Phase 1 leads are preserved and assigned to the `New` pipeline stage.

## Local development

Create and activate a Python 3.12 virtual environment, then install development dependencies:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Create `.env` from `.env.example`. When running the API outside Docker, change the database hostname in `DATABASE_URL` from `db` to `localhost`.

### AI configuration

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `local` | Select `local` or `openai` |
| `AI_ALLOW_FALLBACK` | `true` | Fall back to local intelligence after provider failure |
| `OPENAI_API_KEY` | empty | Optional API key; never commit it |
| `OPENAI_MODEL` | empty | Model available to your OpenAI project |
| `OPENAI_TIMEOUT_SECONDS` | `20` | External provider timeout |

The default local provider is deterministic, explainable, and requires no network access. To opt into OpenAI, set `AI_PROVIDER=openai`, provide the API key and model through `.env`, and restart the API. The OpenAI provider uses the Responses API with a strict JSON schema, disables provider-side response storage for the request, handles timeouts/API failures/malformed output, and never logs the API key or raw request.

Apply migrations from the backend directory:

```bash
cd backend
alembic upgrade head
```

Run the API from the same directory:

```bash
uvicorn app.main:app --reload --port 8001
```

Run the frontend in a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

`NEXT_PUBLIC_API_URL` selects the browser-facing API URL. `CORS_ORIGINS` is a comma-separated backend allowlist; the local default is `http://localhost:3000`. `API_PORT` and `FRONTEND_PORT` configure the Docker host ports.

## Tests

Tests use an isolated in-memory SQLite database and do not alter development data:

```bash
pytest
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

The suites cover scoring, CRUD, pipeline transitions and history, dashboard aggregates, activities, task lifecycle, intelligence, demo data, API client behavior, UI mappings, and critical lead/intelligence rendering.

## API summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Verify API and database connectivity |
| `GET` | `/dashboard/summary` | Read KPI and chart aggregates |
| `GET` | `/leads` | List, search, filter, sort, and paginate leads |
| `POST` | `/leads` | Create and score a lead |
| `GET` | `/leads/{id}` | Retrieve one lead |
| `GET` | `/leads/{id}/detail` | Retrieve lead, recent activity, and upcoming tasks |
| `PATCH` | `/leads/{id}` | Update and rescore a lead |
| `PATCH` | `/leads/{id}/stage` | Transition the pipeline stage and record history |
| `DELETE` | `/leads/{id}` | Delete a lead |
| `POST` | `/leads/{id}/activities` | Add a call, email, meeting, or note |
| `GET` | `/leads/{id}/activities` | Retrieve the lead timeline |
| `GET` | `/activities/{id}` | Retrieve one activity |
| `POST` | `/leads/{id}/tasks` | Create a follow-up task |
| `GET` | `/leads/{id}/tasks` | List one lead's tasks |
| `GET` | `/tasks` | Filter and sort tasks across leads |
| `GET/PATCH/DELETE` | `/tasks/{id}` | Retrieve, update, or delete a task |
| `POST` | `/tasks/{id}/complete` | Complete a task and set `completed_at` |
| `POST` | `/tasks/{id}/cancel` | Cancel a task |
| `POST` | `/leads/{id}/intelligence` | Generate or regenerate structured sales intelligence |
| `GET` | `/leads/{id}/intelligence` | Retrieve the latest stored intelligence |

## AI Sales Intelligence

Intelligence is derived only from known data: Lead profile, score, qualification status, pipeline stage, recent activities, and pending tasks. It does not invent competitors, timelines, or purchasing commitments.

The local provider considers signals such as budget, company size, AI/automation requirements, qualification score, pipeline position, overdue tasks, requirement detail, and recorded sales activity. Recommendations include an explicit reason and priority so they remain advisory and reviewable.

Example response excerpt:

```json
{
  "qualification_summary": "Hot B2B lead for OrbitFlow SaaS with a score of 90/100...",
  "buying_signals": [
    {"signal": "High budget", "evidence": "Stated budget is $9,000."}
  ],
  "risks": [],
  "next_best_action": {
    "action": "Schedule discovery call",
    "reason": "The lead is Qualified with a score of 90/100.",
    "priority": "high"
  },
  "follow_up": {
    "subject": "Next steps for OrbitFlow SaaS",
    "message": "Hi Michael, ..."
  },
  "provider": "local"
}
```

Generate and retrieve intelligence:

```bash
curl -X POST http://localhost:8001/leads/1/intelligence
curl http://localhost:8001/leads/1/intelligence
```

Regeneration updates the existing intelligence record. Only the first generation adds a timeline activity, avoiding repeated activity noise.

## Demo data

Demo data is never inserted during application startup. After applying migrations, explicitly load six fictional B2B scenarios:

```bash
cd backend
python -m app.seed
```

The command is idempotent. Run `python -m app.seed --reset` to replace only the six known demo companies while preserving all other leads. The dataset represents SaaS, construction, digital marketing, e-commerce, technology consulting, and manufacturing businesses across different scores, stages, activities, priorities, and task states.

## Portfolio demo workflow

1. Open the Dashboard and review the live KPIs and distributions.
2. Open **OrbitFlow SaaS** from Leads and inspect its Hot score and Qualified stage.
3. Generate or review Sales Intelligence, buying signals, and the next best action.
4. Copy the personalized follow-up subject and message.
5. Add and complete a lead follow-up task.
6. Move the lead from the Pipeline board.
7. Return to the lead and confirm the stage change in the activity timeline.
8. Return to the Dashboard to see the updated business view.

## Dashboard screenshots

Add final portfolio captures here after starting the seeded stack:

- `docs/screenshots/dashboard.png` — executive KPI and chart view
- `docs/screenshots/lead-detail.png` — CRM record and AI-assisted intelligence
- `docs/screenshots/pipeline.png` — six-stage pipeline board

## Roadmap

- **Phase 1 — complete:** backend foundation, scoring, CRUD, PostgreSQL, migrations, tests, Docker, documentation
- **Phase 2 — complete:** sales pipeline, activity timeline, follow-up tasks, lead detail API, and demo dataset
- **Phase 3 — complete:** provider-based AI sales intelligence, explainable recommendations, follow-up generation, persistence, and fallback handling
- **Phase 4 — complete:** professional full-stack dashboard for leads, pipeline, tasks, timelines, analytics, and intelligence
- **Phase 5:** authentication, ownership, workspaces, ingestion, audit controls, and deployment

No paid API is required for the complete Phase 1–4 demo.
