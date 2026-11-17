# API (Phase 2.1). Interactive docs: http://localhost:8000/docs

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
