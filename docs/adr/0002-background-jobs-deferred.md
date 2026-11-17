# ADR 0002: No Redis/Celery yet
Status: Accepted (Phase 0.1)

**Decision:** Use FastAPI background tasks plus a database-backed job table when needed. Add Redis/Celery only when a measured workload (bulk embedding, large imports) requires it, via a new ADR.
**Why:** Fewer services for a small team before the first lesson exists.
