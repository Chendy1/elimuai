# Database schema (as of migration 0005)

| Table | Purpose | Notes |
|---|---|---|
| `users` | Guardian accounts | email unique, stored lowercase (check constraint); `password_hash` is Argon2id; soft delete via `deleted_at`. Roles arrive in Phase 2.3. |
| `sessions` | Server-side login sessions | Only `sha256(token)` stored; `csrf_token`; absolute expiry; `revoked_at`. |
| `password_reset_tokens` | One-time reset links | Only token hash stored; 30-minute expiry; single use. |
| `learners` | Guardian-managed learner profiles | nickname, grade 4-9 (check constraint); unique nickname per guardian among non-deleted (partial index); soft delete. |
| `consent_records` | Consent evidence | notice version, SHA-256 of the text shown, accepted_at, withdrawn_at. |
| `roles` | The seven platform roles | Seeded by migration; mirrors `ALL_ROLES` in code (tested). |
| `user_roles` | Role assignments | Composite key (user, role). Existing users were backfilled as `guardian`. |
| `audit_logs` | Who did what and when | actor, action, target, JSONB details. No secrets, no children's names. |
| `curricula`, `curriculum_versions` | Curriculum and its versions | version status draft/published/archived; one published version per curriculum (partial unique index). |
| `grades`, `learning_areas`, `units`, `strands`, `sub_strands` | The hierarchy | `units` optional. Each carries review status, reviewer, comment and a source-page reference (not grades). Learning areas can be archived. |
| `topics`, `learning_outcomes`, `learning_experiences`, `key_inquiry_questions` | Sub-strand content | ordered. |
| `core_competencies` (7 seeded), `curriculum_values`, `pertinent_contemporary_issues` + `sub_strand_*` link tables | Competencies, values, PCIs | values and PCIs shared, matched case-insensitively. |
| `rubric_indicators` | Official four-level descriptors per strand | separate from ElimuAI mastery states. |
| `curriculum_sources`, `curriculum_source_pages` | Source documents and page text | licence status; pdf page and printed page stored separately. |

Migrations: `0001` enables pgvector, `0002` creates users, sessions and reset tokens, `0003` creates learners and consent records, `0004` creates roles, user_roles and audit_logs, `0005` creates the curriculum engine tables. Constraint and index names follow the naming convention in `app/models/base.py`.
