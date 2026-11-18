# ADR 0007: Roles in the database, permission matrix in code
Status: Accepted (Phase 2.3a) · Revisit: when admins need to edit permissions at runtime

**Decision:** `roles` and `user_roles` live in PostgreSQL. Which permissions each role grants lives in `app/core/permissions.py` and is enforced by the `require_permission()` dependency on the backend. A test keeps the `roles` table and the code in sync.
**Why:** The matrix changes rarely, should be code-reviewed like any security change, and is easy to unit-test. A database-managed permissions table can be added later if administrators need to edit it.
**Bootstrap:** the first super administrator is created with `python -m app.cli create-superadmin`. Registered users get the `guardian` role automatically; an admin promotes them to other roles. An email-invite flow is a later phase.
**Safeguards:** the last super administrator cannot be demoted; role changes and other sensitive actions are written to `audit_logs` in the same transaction; audit details never contain children's nicknames.

**Own-scoped permissions:** `learners:manage_own` and `learning:use` are granted only by the guardian and student roles. The super administrator holds every administrative permission but is not implicitly a guardian or student; an admin who also looks after children needs the guardian role as well.
