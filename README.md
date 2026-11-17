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
