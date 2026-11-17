# PROJECT_STATE

**Current:** Phase 1.1 verified (CI green, pushed to github.com/Chendy1/elimuai). Phase 1.2 delivered, awaiting verification.
**Next:** Phase 2.1 (guardian registration, login, sessions). Phase 0.2-0.4 spikes run in parallel as inputs arrive.

## Pinned versions
Python 3.12 · Node 22 · PostgreSQL 16 (pgvector/pgvector:pg16) · FastAPI 0.115.6 · SQLAlchemy 2.0.36 · Alembic 1.14.0 · Next.js 15.1.3 · React 19.0.0 · Tailwind 3.4.17

## Decisions
ADR 0001 cookie sessions · ADR 0002 no Redis/Celery yet · ADR 0003 provider adapters

## Verification status
- 1.1: GitHub Actions CI green (backend ruff, alembic upgrade, pytest; frontend lint, typecheck, vitest, build).
- 1.2: built without network access; unverified until CI and local runs pass. Playwright e2e job is new.
- Local Docker run checklist from 1.1 not yet confirmed by owner.
- Known: CI actions (checkout@v4, setup-python@v5) show a Node 20 deprecation notice; bump versions later.

## Inputs needed from owner
- Official KICD curriculum design documents (Grade 6 Maths and English first) and permission status
- Guardian-first consent confirmation, legal contact, DPIA owner
- AI cost ceiling per active learner per month (placeholder USD 0.10)

## Open issues
None yet.

## Compliance tracker
KICD permission: not started · DPAs: not started · DPIA: not started

## Quality gates (actuals)
Not measured yet.

## Notes (Phase 1.2)
- Playwright e2e runs against a production build on port 3100 so it cannot clash with Docker or a dev server on 3000.
- 1.2 verified locally: lint, typecheck, vitest (3), playwright (6). CI result pending.
