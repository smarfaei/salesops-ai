# SalesOps AI

**AI-Powered Lead Qualification & Sales Automation Platform**

SalesOps AI helps sales teams capture, qualify, prioritize, and act on incoming leads. This repository currently contains **Phase 1: Professional Foundation**—a production-style FastAPI backend with deterministic lead scoring, PostgreSQL persistence, migrations, tests, and a reproducible Docker workflow.

## Current features

- Create, retrieve, update, and delete leads
- Explainable 0–100 lead scoring with Hot, Warm, and Cold classifications
- Search across lead name, company, and need
- Filter by lead status
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
│   ├── services/   # lead-scoring business logic
│   └── main.py     # FastAPI application
├── alembic/        # database migrations
├── tests/          # behavior-focused test suite
└── alembic.ini
```

The HTTP layer validates input and coordinates requests. Business scoring lives in one service. SQLAlchemy models handle persistence, while Pydantic schemas define every public API response. Tables are created only through Alembic migrations.

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

The suite covers scoring rules and boundaries, validation, creation, retrieval, updates with score recalculation, missing resources, deletion, search, filtering, sorting, pagination, and health checks.

## API summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Verify API and database connectivity |
| `GET` | `/leads` | List, search, filter, sort, and paginate leads |
| `POST` | `/leads` | Create and score a lead |
| `GET` | `/leads/{id}` | Retrieve one lead |
| `PATCH` | `/leads/{id}` | Update and rescore a lead |
| `DELETE` | `/leads/{id}` | Delete a lead |

## Roadmap

- **Phase 1 — complete:** backend foundation, scoring, CRUD, PostgreSQL, migrations, tests, Docker, documentation
- **Phase 2:** sales pipeline, activity timeline, follow-up tasks, richer lead profiles, authentication and roles
- **Phase 3:** AI qualification summaries, next-best actions, personalized follow-ups, integrations
- **Phase 4:** professional dashboard, analytics, CSV import, deployment and portfolio demo assets

No paid API is required for Phase 1.
