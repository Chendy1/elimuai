# Database schema (as of migration 0002)

| Table | Purpose | Notes |
|---|---|---|
| `users` | Guardian accounts | email unique, stored lowercase (check constraint); `password_hash` is Argon2id; soft delete via `deleted_at`. Roles arrive in Phase 2.3. |
| `sessions` | Server-side login sessions | Only `sha256(token)` stored; `csrf_token`; absolute expiry; `revoked_at`. |
| `password_reset_tokens` | One-time reset links | Only token hash stored; 30-minute expiry; single use. |

Migrations: `0001` enables pgvector, `0002` creates the tables above. Constraint and index names follow the naming convention in `app/models/base.py`.
