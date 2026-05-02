# Apply database migrations so the pipeline can write to bronze/silver/gold/meta.
# Run from project root: .\scripts\run-migrations.ps1
# Requires: docker compose, api and postgres services up.

Set-Location $PSScriptRoot\..

Write-Host "Applying migrations (creates bronze, silver, gold, meta schemas and tables)..."
docker compose exec api alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Write-Host "Migrations OK. You can now trigger the pipeline (Run now) and it should run without schema errors." -ForegroundColor Green
} else {
    Write-Host "Migrations failed. Ensure postgres and api containers are up: docker compose up -d postgres api" -ForegroundColor Red
}
