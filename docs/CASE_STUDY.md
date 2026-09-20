# SalesOps AI — Portfolio Case Study

## Problem

Inbound B2B leads commonly arrive through disconnected channels. Sales teams need a consistent way to qualify opportunities, preserve context, prioritize follow-up, and see pipeline health without relying on subjective spreadsheet workflows.

## Users

- Sales representatives managing daily follow-ups
- Sales managers reviewing qualification and pipeline health
- Small B2B teams that need lightweight sales operations automation

## Business Workflow

```text
Capture Lead → Score → Hot/Warm/Cold → Qualify → Recommend Action
→ Draft Follow-up → Create Task → Move Pipeline → Review Analytics
```

## Solution

SalesOps AI is a responsive CRM-style application built around a single lead record. It combines explainable qualification, a six-stage pipeline, activity history, follow-up tasks, analytics, and advisory sales intelligence. The default intelligence provider runs locally, so the complete demo needs no paid service.

## Architecture

The Next.js frontend calls a typed, centralized FastAPI client. FastAPI validates requests and delegates work to focused scoring, workflow, task, activity, and intelligence services. SQLAlchemy persists records in PostgreSQL, while Alembic manages schema evolution. Docker Compose provides a repeatable local stack.

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
- Authentication and multi-tenancy are intentionally deferred to avoid premature complexity.

## Testing

Pytest covers backend scoring, CRUD, workflow, dashboard aggregates, demo data, and intelligence. Vitest and Testing Library cover API behavior, UI mappings, and critical Lead and Intelligence rendering. CI runs lint, strict typechecking, tests, and a production build.

## Business Value

The project demonstrates how a sales team could make qualification consistent, keep follow-up visible, and turn scattered lead context into a clear next action. It is a portfolio demonstration, not a claim of measured customer outcomes.

## Limitations

- No authentication, ownership, or tenant isolation
- No email sending or external CRM synchronization
- No background job queue or production observability stack
- Scoring weights are code-defined rather than user-configurable
- AI recommendations still require human review

## Future Improvements

Add authentication and workspaces, role-based access, audit controls, configurable scoring, ingestion webhooks, email/CRM integrations, background jobs, and production monitoring after the single-workspace workflow is validated.
