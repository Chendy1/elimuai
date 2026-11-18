# Runs the Playwright tests without clashing with the Docker frontend (they share frontend\.next).
# Run from the project root:  powershell -ExecutionPolicy Bypass -File scripts\test-e2e.ps1
docker compose stop frontend
Push-Location frontend
try { npm run test:e2e } finally {
  Pop-Location
  Remove-Item -Recurse -Force frontend\.next -ErrorAction SilentlyContinue
  docker compose start frontend
}
