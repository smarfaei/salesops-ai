# Deployment Guide

SalesOps AI is portable across container hosts and managed application platforms. A simple production layout is:

```text
Next.js frontend → Vercel or container host
FastAPI backend  → Render, Railway, Fly.io, or container platform
PostgreSQL       → managed PostgreSQL
```

These are examples, not hard requirements.

## Frontend

- Root directory: `frontend`
- Install: `npm ci`
- Build: `npm run build`
- Start for a Node host: `npm run start`
- Required build-time variable: `NEXT_PUBLIC_API_URL=https://api.example.com`
- Recommended Node version: 24

`NEXT_PUBLIC_API_URL` is embedded in browser assets during the production build. Rebuild the frontend when the public API URL changes.

## Backend

- Install: `pip install -r requirements.txt`
- Working directory: `backend`
- Pre-deploy migration: `alembic upgrade head`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health endpoint: `/health`
- Recommended Python version: 3.12

If the platform does not interpolate `$PORT` in a process command, configure its native port setting or provide the equivalent explicit value.

## Required Environment Variables

| Variable                 | Service        | Notes                                                            |
| ------------------------ | -------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`           | Backend        | Managed PostgreSQL URL using the `postgresql+psycopg://` dialect |
| `APP_ENV`                | Backend        | Set to `production`                                              |
| `DEBUG`                  | Backend        | Set to `false`                                                   |
| `CORS_ORIGINS`           | Backend        | Exact comma-separated HTTPS frontend origins                     |
| `NEXT_PUBLIC_API_URL`    | Frontend build | Public HTTPS API origin                                          |
| `AI_PROVIDER`            | Backend        | Keep `local` unless OpenAI is intentionally configured           |
| `AI_ALLOW_FALLBACK`      | Backend        | Recommended `true`                                               |
| `OPENAI_API_KEY`         | Backend        | Optional secret; only for the OpenAI provider                    |
| `OPENAI_MODEL`           | Backend        | Required when using OpenAI                                       |
| `OPENAI_TIMEOUT_SECONDS` | Backend        | Optional; default 20 seconds                                     |

Do not expose `POSTGRES_PASSWORD`, `DATABASE_URL`, or `OPENAI_API_KEY` to the frontend.

## Database Migrations

Run `alembic upgrade head` exactly once per deployment release before accepting API traffic. Use a platform release command or a short-lived migration job when multiple API replicas are deployed.

Do not run demo reset against a production database. Demo data is created only by the explicit `python -m app.seed` command.

## CORS

Set `CORS_ORIGINS` to the exact production frontend origin, for example:

```text
CORS_ORIGINS=https://salesops.example.com
```

Multiple origins are comma-separated. Avoid `*`, especially if credentials are enabled.

## Container Deployment

The repository includes production-oriented backend and frontend Dockerfiles. The frontend image uses the Next.js standalone output, and both runtime images use non-root users. Docker Compose is intended for local/demo operation; managed services should inject secrets through their secret store.

## Production Safety Checklist

- Use a dedicated managed PostgreSQL database with backups and TLS.
- Generate a strong database password; never reuse `.env.example` values.
- Keep `DEBUG=false` and restrict CORS to HTTPS origins.
- Store all secrets in the deployment platform, not Git or build arguments.
- Run migrations before starting the new API release.
- Confirm `/health`, frontend loading, API calls, and intelligence generation after deployment.
- Add authentication and tenant isolation before storing real customer data.
- Add rate limiting, monitoring, error reporting, and a backup restore test before public production use.

## Post-Deploy Smoke Test

1. Check `GET /health` returns database connected.
2. Load the Dashboard from the production frontend.
3. Create a disposable non-sensitive lead and verify scoring.
4. Generate local intelligence and verify the advisory label.
5. Create/complete a task and change a pipeline stage.
6. Remove the disposable record through an approved administrative workflow.
