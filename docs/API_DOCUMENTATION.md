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

## Roles and administration (Phase 2.3a)

`/auth/login` and `/auth/me` now also return `roles`. Learner endpoints require the `guardian` role (permission `learners:manage_own`); a signed-in user without it gets 403.

| Method and path | Permission | Result |
|---|---|---|
| GET `/admin/roles` | `users:read` | role -> permissions matrix |
| GET `/admin/users?limit&offset` | `users:read` | users with roles (limit 1-100) |
| PUT `/admin/users/{id}/roles` | `users:manage_roles` + CSRF | body `{roles:[...]}`; 409 if it would remove the last super_admin; 422 unknown role |
| GET `/admin/audit-logs?limit&offset&action` | `audit:read` | newest first |

Create the first super administrator (prompts for a password):
`docker compose exec -it backend python -m app.cli create-superadmin --email you@example.com`

## Curriculum (Phase 3.1)

Admin endpoints are under `/admin/curriculum` (structure: `curriculum:manage`; review: `content:review`; publish/archive: `content:publish`; writes need CSRF). Errors: 404 not found, 409 conflict (duplicate, read-only version, failed publish gate; publish failures return `detail: {message, details}`).

| Method and path | Purpose |
|---|---|
| GET/POST `/curricula`, GET/POST `/curricula/{id}/versions` | curricula and draft versions |
| POST `/versions/{id}/grades`, POST `/grades/{id}/learning-areas`, PATCH `/learning-areas/{id}` | grades, learning areas (rename, reorder, archive) |
| POST `/learning-areas/{id}/units`, `/learning-areas/{id}/strands` | optional units, strands (with rubric) |
| POST `/strands/{id}/sub-strands` | sub-strand with topics, outcomes, experiences, questions, competencies, values, PCIs |
| GET `/versions/{id}/tree` | whole version with review status |
| POST `/review` | `{kind, id, status, comment}` |
| POST `/versions/{id}/publish`, `/archive` | publishing gates: all approved, not empty, all sources licensed |
| GET/POST `/sources`, PATCH `/sources/{id}/license` | source documents and permission status |

Learner reads (signed in, published only): GET `/curriculum/grades`, `/curriculum/grades/{level}/learning-areas`, `/curriculum/learning-areas/{id}`.

### Source pages (Phase 3.2a)
`GET /admin/curriculum/sources/{id}/pages?offset&limit` (page numbers and sizes) and `GET /admin/curriculum/sources/{id}/pages/{pdf_page}` (stored text). Permission `content:review`, so reviewers can read source pages next to draft records. Import itself is a CLI command (see `docs/CURRICULUM_IMPORT_GUIDE.md`).

### Editing (Phase 3.4)
`PATCH /admin/curriculum/sub-strands/{id}` and `PATCH /admin/curriculum/strands/{id}` (`curriculum:manage` + CSRF). Only the fields sent change; a list that is sent replaces the whole list. Any edit resets the record to `draft`, writes a `curriculum.*_edited` audit event (field names only) and is refused on published or archived versions.
