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

| Variable                          | Service        | Notes                                                            |
| --------------------------------- | -------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`                    | Backend        | Managed PostgreSQL URL using the `postgresql+psycopg://` dialect |
| `APP_ENV`                         | Backend        | Set to `production`                                              |
| `DEBUG`                           | Backend        | Set to `false`                                                   |
| `DEMO_MODE`                       | Backend        | Set to `true` only for the isolated public portfolio demo        |
| `DEMO_RATE_LIMIT_REQUESTS`        | Backend        | Maximum demo writes per client IP in each window; default `60`   |
| `DEMO_RATE_LIMIT_WINDOW_SECONDS`  | Backend        | Rate-limit window; default `60`                                  |
| `CORS_ORIGINS`                    | Backend        | Exact comma-separated HTTPS frontend origins                     |
| `JWT_SECRET`                      | Backend        | Random signing secret, at least 32 characters                    |
| `ACCESS_TOKEN_MINUTES`            | Backend        | Access JWT lifetime; default `15`                                |
| `REFRESH_TOKEN_DAYS`              | Backend        | Refresh-session lifetime; default `7`                            |
| `REFRESH_COOKIE_NAME`             | Backend        | Refresh cookie name; default `salesops_refresh`                  |
| `AUTH_COOKIE_SECURE`              | Backend        | Must be `true` in production                                     |
| `AUTH_COOKIE_SAMESITE`            | Backend        | `lax`, `strict`, or `none`; `none` requires Secure               |
| `LOGIN_RATE_LIMIT_REQUESTS`       | Backend        | Login attempts per client/window; default `5`                    |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Backend        | Login-limit window; default `60`                                 |
| `DEMO_ACCOUNT_PASSWORD`           | Backend seed   | Explicit public-demo password; never a production default        |
| `NEXT_PUBLIC_API_URL`             | Frontend build | Public HTTPS API origin                                          |
| `NEXT_PUBLIC_DEMO_MODE`           | Frontend build | Set to `true` with the backend public-demo deployment            |
| `AI_PROVIDER`                     | Backend        | Keep `local` unless OpenAI is intentionally configured           |
| `AI_ALLOW_FALLBACK`               | Backend        | Recommended `true`                                               |
| `OPENAI_API_KEY`                  | Backend        | Optional secret; only for the OpenAI provider                    |
| `OPENAI_MODEL`                    | Backend        | Required when using OpenAI                                       |
| `OPENAI_TIMEOUT_SECONDS`          | Backend        | Optional; default 20 seconds                                     |

Do not expose `POSTGRES_PASSWORD`, `DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, access tokens, or refresh tokens to frontend configuration or logs.

## Authentication and Cookie Deployment

Access JWTs are short-lived and held in browser memory. Refresh credentials are opaque random values stored only in a path-scoped `HttpOnly` cookie; the database stores only their SHA-256 hashes. Every refresh rotates the credential and revokes its predecessor. Logout revokes the active session.

For a same-site deployment, prefer `AUTH_COOKIE_SAMESITE=lax`. If the frontend and API require a cross-site cookie, use HTTPS and `AUTH_COOKIE_SAMESITE=none`; configuration validation rejects `none` without a Secure cookie. Production mode forces `AUTH_COOKIE_SECURE=true`. `CORS_ORIGINS` must contain the exact frontend origins because credentialed CORS is enabled.

## Public Portfolio Demo Mode

Use a dedicated database that contains no customer or personal data. Configure:

```text
APP_ENV=production
DEBUG=false
DEMO_MODE=true
NEXT_PUBLIC_DEMO_MODE=true
AI_PROVIDER=local
CORS_ORIGINS=https://your-frontend.example
JWT_SECRET=<at-least-32-random-characters-from-the-platform-secret-store>
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=lax
DEMO_ACCOUNT_PASSWORD=<an-intentionally-public-demo-only-password>
```

Do not configure `OPENAI_API_KEY` for the public demo. When `DEMO_MODE=true`, the backend forces the local provider, clears OpenAI configuration in application settings, forces debug off, disables lead creation/edit/deletion and task deletion, and removes `/docs`, `/redoc`, and `/openapi.json`. Pipeline changes, demo activities, demo tasks, and local intelligence remain available. The UI tells visitors to use fictional data only. A lightweight in-memory rate limit protects state-changing requests; use a gateway-level limiter as well if the demo receives significant traffic or runs with multiple API replicas.

After migrations, initialize or restore the dedicated demo database explicitly:

```bash
cd backend
python -m app.seed --reset --with-intelligence --with-users
```

The reset command and demo-account seed both refuse to run unless `DEMO_MODE=true`. In demo mode it deletes all rows from the dedicated lead dataset, recreates only the six fictional scenarios, creates the four documented `@salesops.demo` accounts, and assigns leads to the fictional Sales Rep. Publish the chosen demo-only password next to the demo URL, but never commit it or reuse it. Never point a demo-mode deployment at a customer or production database.

Public-demo restrictions take precedence over account privileges: `DEMO_MODE → authentication → RBAC → ownership`. Even the Admin Demo account cannot delete or permanently rewrite the canonical lead set. API documentation remains unavailable in demo mode so destructive operations are not advertised publicly.

## Database Migrations

Run `alembic upgrade head` exactly once per deployment release before accepting API traffic. Use a platform release command or a short-lived migration job when multiple API replicas are deployed.

Do not run demo reset against a customer database. Demo data is created only by the explicit guarded command documented above.

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
- Rotate `JWT_SECRET` and invalidate refresh sessions after any suspected disclosure.
- Confirm the refresh cookie is `HttpOnly`, `Secure`, correctly scoped, and never visible to JavaScript.
- Run migrations before starting the new API release.
- Confirm `/health`, frontend loading, API calls, and intelligence generation after deployment.
- Keep the public demo database isolated and fictional; add tenant isolation before storing data for multiple customers.
- The built-in limiter is process-local. Add gateway/distributed rate limiting, monitoring, error reporting, and a backup restore test before production use.

## Post-Deploy Smoke Test

1. Check `GET /health` returns database connected.
2. Login as Viewer and confirm the interface is read-only.
3. Login as Sales Rep and confirm only assigned leads can be opened or changed.
4. Login as Manager and confirm assignment and audit access without user administration.
5. Login as Admin and confirm Users and Audit Logs are available.
6. Confirm lead creation/edit/deletion, task deletion, and API docs return `403`/`404` in demo mode as appropriate.
7. Generate local intelligence, create/complete a task, add an activity, and change a pipeline stage.
8. Run the guarded reset and confirm the six fictional records and four role accounts are restored.
