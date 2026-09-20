# SalesOps AI — Portfolio Case Study

## Problem

Inbound B2B leads commonly arrive through disconnected channels. Sales teams need a consistent way to qualify opportunities, preserve context, prioritize follow-up, and see pipeline health without relying on subjective spreadsheet workflows.

## Users

- Sales representatives managing daily follow-ups
- Sales managers reviewing qualification and pipeline health
- Small B2B teams that need lightweight sales operations automation
- Administrators controlling access and Managers assigning opportunities

## Business Workflow

```text
Capture Lead → Score → Hot/Warm/Cold → Qualify → Recommend Action
→ Draft Follow-up → Create Task → Move Pipeline → Review Analytics
```

## Solution

SalesOps AI is a responsive CRM-style application built around a single lead record. It combines explainable qualification, a six-stage pipeline, activity history, follow-up tasks, analytics, and advisory sales intelligence. The default intelligence provider runs locally, so the complete demo needs no paid service.

## Architecture

The Next.js frontend calls a typed, centralized FastAPI client. FastAPI authenticates each request, applies centralized role and ownership policies, then delegates work to focused scoring, workflow, task, activity, and intelligence services. SQLAlchemy persists records, hashed refresh sessions, and audit events in PostgreSQL, while Alembic manages schema evolution. Docker Compose provides a repeatable local stack.

## Authentication, RBAC, and Ownership

The application uses short-lived access JWTs held in browser memory and rotating opaque refresh tokens delivered through a scoped `HttpOnly` cookie. Only hashes of refresh tokens and salted `scrypt` password hashes are stored. Protected content waits for session restoration, avoiding a flash of private UI.

An explicit permission map defines Admin, Sales Manager, Sales Rep, and Viewer capabilities. Admins manage users; Managers assign leads and inspect audit events; Sales Reps work only on assigned leads; Viewers receive a read-only sales view. Backend policy is authoritative even when client-side controls are manipulated.

Meaningful actions produce audit records with actor, event, entity, timestamp, and sanitized metadata. Passwords, tokens, API keys, and authorization headers are excluded.

## Lead Scoring

The authoritative backend policy calculates a 0–100 score from stated budget, company size, and an AI requirement. Every point contribution is returned as a human-readable reason. Thresholds classify leads as Hot, Warm, or Cold; the frontend displays the result but does not duplicate scoring rules.

## AI Sales Intelligence

Intelligence uses only known lead fields, recent activities, open tasks, score, and pipeline stage. Its structured output contains a qualification summary, evidence-backed buying signals and risks, a reasoned next best action, and a follow-up draft. The UI labels this content as an **AI-assisted recommendation**.

## Provider Architecture

A provider interface separates orchestration from generation. The deterministic local provider supports offline demos and tests. An optional OpenAI provider uses structured validation, timeouts, and local fallback without changing the product workflow.

## Pipeline Automation

Leads move through New, Qualified, Contacted, Proposal, Won, and Lost. Every successful stage change is persisted and recorded in the activity timeline, creating an auditable business history.

## Tasks

Tasks belong to a lead and support priority, due date, editing, completion, cancellation, deletion, and pending/upcoming/overdue views. Overdue work remains visible without aggressive visual treatment.

## Analytics

The dashboard reads backend aggregates for lead qualification, stage distribution, score bands, task status, open pipeline value, and operational KPIs. Metrics are descriptive and make no revenue or conversion claims.

## Technical Decisions

- Business rules remain in backend services rather than UI components.
- The local provider makes the core demo deterministic and cost-free.
- Latest intelligence is persisted for fast display and explicit regeneration.
- A centralized API client prevents scattered request logic.
- Lightweight React hooks are sufficient; a global state library is unnecessary.
- Authentication remains single-workspace by design; tenant isolation is deferred until a multi-tenant product phase.

## Testing

Pytest covers backend scoring, CRUD, workflow, dashboard aggregates, demo data, intelligence, authentication, token lifecycle, RBAC, ownership, audit events, and demo-mode precedence. Vitest and Testing Library cover API behavior, session state, protected routes, role-aware UI, and critical Lead and Intelligence rendering. CI runs lint, strict typechecking, tests, and a production build.

## Business Value

The project demonstrates how a sales team could make qualification consistent, keep follow-up visible, and turn scattered lead context into a clear next action. It is a portfolio demonstration, not a claim of measured customer outcomes.

## Limitations

- No tenant isolation, registration, password recovery, or email verification
- No email sending or external CRM synchronization
- No background job queue or production observability stack
- Scoring weights are code-defined rather than user-configurable
- AI recommendations still require human review

## Future Improvements

Add workspaces and tenant isolation, password recovery, configurable scoring, ingestion webhooks, email/CRM integrations, background jobs, distributed rate limiting, and production monitoring after the single-workspace workflow is validated.
