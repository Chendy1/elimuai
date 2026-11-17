# API (Phase 2.1). Interactive docs: http://localhost:8000/docs

From the browser, every path below is prefixed with `/api` (for example `/api/auth/login`) and proxied to the backend.

Authentication uses an httpOnly `elimu_session` cookie. State-changing authenticated requests must send the header `X-CSRF-Token` (value returned by login and `/auth/me`).

| Method and path | Auth | Result |
|---|---|---|
| POST `/auth/register` | none | 201 user; 409 if email exists; 422 weak password; 429 rate limit |
| POST `/auth/login` | none | 200 `{user, csrf_token}` and session cookie; 401 generic error; 429 |
| GET `/auth/me` | cookie | 200 `{user, csrf_token}`; 401 |
| POST `/auth/logout` | cookie + CSRF | 204 and cookie cleared; 401/403 |
| POST `/auth/password-reset/request` | none | 202 always (never reveals whether the account exists) |
| POST `/auth/password-reset/confirm` | none | 204; 400 invalid or expired; 422 weak password. Revokes all sessions. |

Password rules: 10 to 128 characters, not a common password, not the email address.
Development email: reset links are printed to the backend log (`docker compose logs backend`).

## Learners (Phase 2.2a)

All require a session; POST, PATCH and DELETE also need `X-CSRF-Token`. Another guardian's learner always returns 404.

| Method and path | Result |
|---|---|
| GET `/learners/consent-notice` | public; current notice `{version, title, text, is_draft}` (draft placeholder) |
| GET `/learners` | your active learners |
| POST `/learners` | body `{nickname, grade 4-9, consent:{notice_version, accepted:true}}` -> 201; 409 notice changed, limit (6) or duplicate nickname; 422 invalid |
| GET `/learners/{id}` | one learner or 404 |
| PATCH `/learners/{id}` | `{nickname?, grade?}` |
| DELETE `/learners/{id}` | 204; soft delete and consent withdrawn |
