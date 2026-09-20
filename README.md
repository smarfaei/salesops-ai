# SalesOps AI

**AI-Powered Lead Qualification & Sales Automation Platform**

SalesOps AI helps sales teams capture, qualify, prioritize, and act on incoming leads. The project currently contains **Phase 2: Sales Workflow**—a production-style mini CRM backend with explainable lead scoring, pipeline management, activity history, follow-up tasks, PostgreSQL persistence, migrations, tests, and a reproducible Docker workflow.

## Current features

- Create, retrieve, update, and delete leads
- Explainable 0–100 lead scoring with Hot, Warm, and Cold classifications
- Six-stage sales pipeline: New, Qualified, Contacted, Proposal, Won, and Lost
- Automatic and manual lead activity timeline
- Follow-up tasks with priorities, lifecycle states, overdue and upcoming views
- Lead detail view model for a future professional frontend
- Search across lead name, company, and need
- Filter by qualification status, pipeline stage, and score range
- Pagination and safe field-based sorting
- Consistent validation and error responses
- PostgreSQL health check and structured application logging
- Alembic-managed database schema
- Automated API and scoring tests

## Technology stack

- Python 3.12
- FastAPI and Pydantic
- SQLAlchemy 2.x and PostgreSQL 16
- Alembic migrations
- Pytest and FastAPI TestClient
- Docker Compose

## Architecture

```text
backend/
├── app/
│   ├── api/        # routes and HTTP error handling
│   ├── core/       # settings and logging
│   ├── db/         # SQLAlchemy base and sessions
│   ├── models/     # persistence models
│   ├── schemas/    # request and response contracts
│   ├── services/   # scoring, pipeline, activity, and task business logic
│   ├── seed.py     # explicit, idempotent portfolio demo data
│   └── main.py     # FastAPI application
├── alembic/        # database migrations
├── tests/          # behavior-focused test suite
└── alembic.ini
```

The HTTP layer validates input and coordinates requests. Business rules live in focused service modules. SQLAlchemy models define `Lead → Activities` and `Lead → Tasks` relationships with database-enforced cascading. Pydantic schemas define every public API response. Tables are created only through Alembic migrations.

## Quick start with Docker

1. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

2. Replace the example password in `.env` and make the password in `DATABASE_URL` match.

3. Build and start PostgreSQL and the API:

   ```bash
   docker compose up --build
   ```

The API is available at `http://localhost:8000`. Interactive OpenAPI documentation is at `http://localhost:8000/docs`; the alternative documentation is at `http://localhost:8000/redoc`.

Compose applies all pending migrations before starting the API. Existing Phase 1 leads are preserved and assigned to the `New` pipeline stage.

## Local development

Create and activate a Python 3.12 virtual environment, then install development dependencies:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Create `.env` from `.env.example`. When running the API outside Docker, change the database hostname in `DATABASE_URL` from `db` to `localhost`.

Apply migrations from the backend directory:

```bash
cd backend
alembic upgrade head
```

Run the API from the same directory:

```bash
uvicorn app.main:app --reload
```

## Tests

Tests use an isolated in-memory SQLite database and do not alter development data:

```bash
pytest
```

The suite covers scoring, Phase 1 CRUD, pipeline transitions and history, activities, task lifecycle and filtering, lead details, demo data, cascading deletes, validation, pagination, and health checks.

## API summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Verify API and database connectivity |
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

## Demo data

Demo data is never inserted during application startup. After applying migrations, explicitly load six fictional B2B scenarios:

```bash
cd backend
python -m app.seed
```

The command is idempotent. Run `python -m app.seed --reset` to replace only the six known demo companies while preserving all other leads. The dataset represents SaaS, construction, digital marketing, e-commerce, technology consulting, and manufacturing businesses across different scores, stages, activities, priorities, and task states.

## Example workflow

1. Create Michael Brown at Acme Technologies with `POST /leads`.
2. Inspect the calculated score, qualification status, reasons, and default `New` stage.
3. Move the lead to `Qualified` with `PATCH /leads/{id}/stage`.
4. Retrieve the automatically recorded stage-change activity.
5. Add a discovery-call task with `POST /leads/{id}/tasks`.
6. Complete it with `POST /tasks/{id}/complete` and verify `completed_at`.
7. Move the lead to `Contacted` and retrieve the complete lead detail view.

## Roadmap

- **Phase 1 — complete:** backend foundation, scoring, CRUD, PostgreSQL, migrations, tests, Docker, documentation
- **Phase 2 — complete:** sales pipeline, activity timeline, follow-up tasks, lead detail API, and demo dataset
- **Phase 3:** authentication and roles, ownership, CSV/webhook ingestion, audit controls, and analytics foundations
- **Phase 4:** AI qualification summaries, next-best actions, personalized follow-ups, and integrations
- **Phase 5:** professional dashboard, deployment, and portfolio demo assets

No paid API is required for Phase 1 or Phase 2.
