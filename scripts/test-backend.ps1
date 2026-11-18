# Installs dev tools in the backend container (they are lost on rebuild) and runs lint + tests.
# Run from the project root:  powershell -ExecutionPolicy Bypass -File scripts\test-backend.ps1
docker compose exec backend sh -c "pip install -q --root-user-action=ignore -r requirements-dev.txt && ruff check . && pytest -q"
