# ADR 0004: In-process rate limiting for now
Status: Accepted (Phase 2.1) · Revisit: when running more than one API instance

**Decision:** Sliding-window limiter in process memory (`app/core/rate_limit.py`) on register, login, and password-reset endpoints.
**Why:** No extra infrastructure before launch.
**Limits:** counters are per process and reset on restart; per-email login limits let an attacker briefly lock out a known address (accepted trade-off, 15-minute window). Move to Redis with the first multi-instance deployment.
