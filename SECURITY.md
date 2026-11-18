# Security notes (living document)

Implemented in Phase 2.1: Argon2id password hashing; opaque random session tokens stored only as SHA-256 hashes; httpOnly + SameSite=Lax cookies (Secure outside development); CSRF header check on authenticated state changes; generic login errors with comparable timing; non-enumerating password reset; reset revokes all sessions; rate limits (ADR 0004).

Known gaps, tracked for later phases: email verification; account lockout notifications; trusted-proxy IP handling; shared rate-limit store; production email provider (the app refuses to send reset email when `APP_ENV=production` until one is configured); registration reveals whether an email exists (409), which email verification would close.

Added in Phase 2.3a: role-based access control enforced in the backend (`require_permission`), least-privilege role matrix, protection of the last super administrator, and an audit log written in the same transaction as the change. Known gaps: audit log is not yet tamper-evident or exportable; no admin-initiated account suspension endpoint yet; no email-invite flow for staff accounts.
