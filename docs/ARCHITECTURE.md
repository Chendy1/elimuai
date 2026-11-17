# Architecture (Phase 1.1)

```
Browser ── Next.js (3000) ──HTTP──▶ FastAPI (8000) ──▶ PostgreSQL 16 + pgvector (5432)
```

- `frontend/`: Next.js 15, React 19, TypeScript, Tailwind 3. Brand colours defined in `tailwind.config.ts`.
- `backend/`: FastAPI. `app/api` (routes), `app/core` (config), `app/db` (session). Migrations in `alembic/`.
- AI services arrive in Phase 5 under `backend/app/ai/` (see ADR 0003).
- Decisions: `docs/adr/`.
