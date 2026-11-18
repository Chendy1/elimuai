# ElimuAI

Free, curriculum-aligned AI learning for Kenyan learners (Grades 4-9). Foundation build; contains no learning content yet.

## Requirements
Docker Desktop (WSL2), Git. Optional for running outside Docker: Python 3.12, Node 22.

## Run (PowerShell, from the project root)
```powershell
Copy-Item .env.example .env
docker compose up --build -d db backend frontend
docker compose exec backend alembic upgrade head
```
- Frontend: http://localhost:3000 · API: http://localhost:8000/health · Readiness: http://localhost:8000/health/ready · API docs: http://localhost:8000/docs

## Tests
```powershell
docker compose exec backend sh -c "pip install -q -r requirements-dev.txt && ruff check . && pytest"
docker compose exec frontend sh -c "npm run lint && npm run typecheck && npm test"
```
See `PROJECT_STATE.md`, `docs/ARCHITECTURE.md` and `docs/adr/`.

## Day-to-day tips (Windows)
- Dev tools in the backend container are lost when the image is rebuilt. Use `powershell -ExecutionPolicy Bypass -File scripts\test-backend.ps1` to reinstall them and run lint and tests.
- `npm run test:e2e` builds into `frontend\.next`, which the Docker frontend also uses. Use `scripts\test-e2e.ps1`, which stops the Docker frontend, runs the tests, clears `.next` and restarts it.
- The Docker frontend can take minutes to start (it runs `npm install` on a bind mount). Faster: `docker compose stop frontend`, then in `frontend`: `$env:BACKEND_URL = "http://localhost:8000"; npm run dev`.
