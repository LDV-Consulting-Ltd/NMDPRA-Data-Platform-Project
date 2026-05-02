# Fix "Pipeline trigger failed" (401): enable Airflow Basic auth, sync admin user, restart API.
# Run from project root: .\scripts\fix-airflow-admin.ps1

Set-Location $PSScriptRoot\..

Write-Host "Step 1/4: Restarting Airflow webserver (enables REST API Basic auth)..."
docker compose up -d airflow-webserver --force-recreate
Start-Sleep -Seconds 15

Write-Host "Step 2/4: Reading password from .env..."
# Use same password as .env so API and Airflow always match
if (Test-Path .env) {
    $envContent = Get-Content .env -Raw
    if ($envContent -match 'AIRFLOW_PASSWORD=(.+)') {
        $password = $matches[1].Trim().Trim('"').Trim("'")
        # trim comment if present
        if ($password -match '^([^\s#]+)') { $password = $matches[1] }
    }
}
if (-not $password) { $password = 'ldvconsulting2026' }
Write-Host "Using AIRFLOW_PASSWORD from .env (length $($password.Length))."

Write-Host "Step 3/4: Syncing Airflow admin user..."
Write-Host "  Deleting existing admin..."
$null = docker compose exec -T airflow-webserver airflow users delete -u admin 2>&1

Write-Host "  Creating admin (info@ldvconsultingltd.ng)..."
docker compose exec -T airflow-webserver airflow users create -r Admin -u admin -e info@ldvconsultingltd.ng -f admin -l user -p $password
if ($LASTEXITCODE -ne 0) {
    Write-Host "Create failed (exit $LASTEXITCODE). Fix errors above and re-run." -ForegroundColor Red
    exit 1
}

Write-Host "Step 4/4: Recreating API and verifying..."
docker compose up -d api --force-recreate
Start-Sleep -Seconds 3
$py = "import os,urllib.request,base64; u=os.environ.get('AIRFLOW_USERNAME','admin'); p=os.environ.get('AIRFLOW_PASSWORD',''); url=os.environ.get('AIRFLOW_API_BASE','http://airflow-webserver:8080/api/v1').rstrip('/')+'/dags/nmdpra_end_to_end_dag/dagRuns?limit=1'; req=urllib.request.Request(url); req.add_header('Authorization','Basic '+base64.b64encode((u+':'+p).encode()).decode()); r=urllib.request.urlopen(req,timeout=10); print(r.getcode())"
$code = docker compose exec -T api python -c $py 2>&1
if ($code -match '^\d+$' -and [int]$code -lt 400) {
    Write-Host "OK: API can reach Airflow (HTTP $code). Try 'Run now' on the dashboard." -ForegroundColor Green
} else {
    Write-Host "Warning: API still got 401. Ensure docker-compose has AIRFLOW__API__AUTH_BACKENDS and AIRFLOW_USERNAME/PASSWORD for api service." -ForegroundColor Yellow
}
Write-Host "Done."
