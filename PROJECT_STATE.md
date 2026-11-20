# PROJECT_STATE

**Current:** Phase 3.3 (curriculum review screens, reviewer read access, CLI create commands) delivered, awaiting verification. Owner has not yet reported results for 3.2a/3.2b.
**Decision (owner):** KICD permission will be requested before deployment/go-live. Until then curriculum data stays in the local development database only; the publishing gate stays enforced in code. Draft letter prepared.
**Next:** 3.2c English parser (themes layout), content editing screen, then Phase 4 (lessons and learner navigation).

## Pinned versions
Python 3.12 · pypdf 5.9.0 · Node 22 · PostgreSQL 16 (pgvector/pgvector:pg16) · FastAPI 0.115.6 · SQLAlchemy 2.0.36 · Alembic 1.14.0 · Next.js 15.1.3 · React 19.0.0 · Tailwind 3.4.17

## Decisions
ADR 0001 cookie sessions · ADR 0002 no Redis/Celery yet · ADR 0003 provider adapters · ADR 0004 in-process rate limiting · ADR 0005 same-origin API proxy · ADR 0006 guardian-managed learners · ADR 0007 RBAC matrix in code · ADR 0008 curriculum model and publishing gates

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
- Staff invitations by email not built; admins promote registered users (ADR 0007).
- Email verification not built; production email provider needed before launch (app refuses to send in production).
- Auth tests use a separate database `<name>_test`, created automatically.
- Phase 1.2 PR: CI result not yet reported by owner.

## Compliance tracker
Consent notice text: DRAFT placeholder in app/consent.py (needs legal review + DPIA) · KICD permission: NOT requested yet. Source PDFs received (Grade 6 Mathematics 2024 revision; Grade 6 English), kept in git-ignored data/sources. Publishing is blocked in code until a source's licence_status is granted · DPAs: not started · DPIA: not started

## Quality gates (actuals)
Not measured yet.
