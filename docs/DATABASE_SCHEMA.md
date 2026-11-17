# Database schema (as of migration 0003)

| Table | Purpose | Notes |
|---|---|---|
| `users` | Guardian accounts | email unique, stored lowercase (check constraint); `password_hash` is Argon2id; soft delete via `deleted_at`. Roles arrive in Phase 2.3. |
| `sessions` | Server-side login sessions | Only `sha256(token)` stored; `csrf_token`; absolute expiry; `revoked_at`. |
| `password_reset_tokens` | One-time reset links | Only token hash stored; 30-minute expiry; single use. |
| `learners` | Guardian-managed learner profiles | nickname, grade 4-9 (check constraint); unique nickname per guardian among non-deleted (partial index); soft delete. |
| `consent_records` | Consent evidence | notice version, SHA-256 of the text shown, accepted_at, withdrawn_at. |

Migrations: `0001` enables pgvector, `0002` creates users, sessions and reset tokens, `0003` creates learners and consent records. Constraint and index names follow the naming convention in `app/models/base.py`.
