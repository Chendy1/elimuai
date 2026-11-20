# Changelog
## 0.11.0 (Phase 3.3)
- Admin review UI (/admin/curriculum): version list, tree navigation, draft record beside its source page, approve / needs changes / in review, publish with explained failures. Reviewers can read curricula, versions, trees and source pages; approving without a comment keeps importer notes; GET /source-pages/{id}; CLI create-curriculum and create-version.

## 0.10.0 (Phase 3.2b)
- Design-table parser (Grade 6 Mathematics layout), propose_from_source service and CLI (dry run supported), synthetic layout fixtures, parser and proposer tests. CLI now explains invalid ids.

## 0.9.0 (Phase 3.2a)
- PDF source importer: pdf_text extraction, import_pdf service (idempotent by SHA-256), CLI import-source / list-sources / show-page, reviewer page-read endpoints, test PDF factory, import guide.

## 0.8.0 (Phase 3.1)
- Curriculum engine: versions, grades, learning areas, optional units, strands, sub-strands and content, rubrics, sources with licence status; review workflow; publishing gates; admin and learner APIs; migration 0005; ADR 0008.

## 0.7.0 (Phase 2.3a)
- RBAC: roles, user_roles, permission matrix, require_permission; audit_logs; /admin API; create-superadmin CLI; migration 0004; ADR 0007.

## 0.6.0 (Phase 2.2b)
- /learners page: list, add (with consent notice and checkbox), edit, remove with confirmation; account link; unit and Playwright tests; helper scripts.

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
