# PROJECT_STATE

**Current:** Phase 0.1 + 1.1 delivered, awaiting user verification.
**Next:** Phase 1.2 (design system, public site skeleton, Playwright smoke test). Phase 0.2-0.4 spikes run in parallel as inputs arrive.

## Pinned versions
Python 3.12 · Node 22 · PostgreSQL 16 (pgvector/pgvector:pg16) · FastAPI 0.115.6 · SQLAlchemy 2.0.36 · Alembic 1.14.0 · Next.js 15.1.3 · React 19.0.0 · Tailwind 3.4.17

## Decisions
ADR 0001 cookie sessions · ADR 0002 no Redis/Celery yet · ADR 0003 provider adapters

## Verification limits of this delivery
Built in an environment with no network, Docker or Postgres. Only Python syntax compilation was run. Backend tests, frontend lint/typecheck/tests/build, Docker and migrations are UNVERIFIED until you run them.
No `package-lock.json` yet: generated on your first `npm install`; commit it.

## Inputs needed from owner
- Official KICD curriculum design documents (Grade 6 Maths and English first) and permission status
- Guardian-first consent confirmation, legal contact, DPIA owner
- AI cost ceiling per active learner per month (placeholder USD 0.10)
- GitHub repo name/URL

## Open issues
None yet.

## Compliance tracker
KICD permission: not started · DPAs: not started · DPIA: not started

## Quality gates (actuals)
Not measured yet.
