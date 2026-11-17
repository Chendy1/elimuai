# ADR 0005: Browser talks to the API through the Next.js server (`/api/*`)
Status: Accepted (Phase 2.1b)

**Decision:** `next.config.mjs` rewrites `/api/:path*` to the FastAPI backend (`BACKEND_URL`). The browser only ever calls its own origin.
**Why:** session cookies stay first-party (no cross-site cookie rules), no CORS in the browser path, simpler HTTPS and a single domain in production (ADR 0001 assumed shared domain).
**Trade-offs:** all API traffic passes through the Next.js server; in production, routing `/api/*` at the load balancer is an equivalent alternative. `BACKEND_URL` is read when Next.js starts (dev) or builds (production).
