# Changelog
## 0.5.0 (Phase 2.2a)
- Learner profiles and versioned consent records: /learners API, migration 0003, ownership isolation, limits, tests, ADR 0006.

## 0.4.0 (Phase 2.1b)
- Pages: register, login, forgot/reset password, account; /api proxy (ADR 0005); client validation; unit and Playwright tests (API mocked).

## 0.3.0 (Phase 2.1a)
- Guardian auth API: register, login, logout, me, password reset; users/sessions/reset-token tables (migration 0002); Argon2id; CSRF; rate limiting; ADR 0004.

## 0.2.0 (Phase 1.2)
- Design system (Plus Jakarta Sans, brand tokens, Button/Container/SectionHeading/header/footer), public pages: home, how it works, start, privacy and terms placeholders. Playwright smoke tests and CI e2e job.

## 0.1.0 (Phase 0.1 + 1.1)
- Repository, Docker Compose (Postgres+pgvector, FastAPI, Next.js), health endpoints, Alembic with pgvector migration, CI, ADRs 0001-0003.
