# ADR 0001: Authentication uses server-side sessions in httpOnly cookies
Status: Accepted (Phase 0.1) · Revisit: Phase 2.1

**Decision:** Secure, httpOnly, SameSite cookies carrying an opaque session ID stored server-side, with CSRF tokens on state-changing requests.
**Why:** Learners are children; tokens in localStorage are exposed to XSS. Server-side sessions can be revoked instantly (guardian removes access, account deletion).
**Trade-off:** Needs a session table and CSRF handling; frontend and API must share a registrable domain in production.
