# Reconstruit l'image Docker rag-api (inclut api/auth LDAP) et redémarre le conteneur
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Test-DockerEngine {
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        docker version 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $saved
    }
}

if (-not (Test-DockerEngine)) {
    Write-Host "Docker Desktop n'est pas démarré." -ForegroundColor Red
    exit 1
}

Write-Host ">>> Build image rag-api:local (sans cache)..." -ForegroundColor Cyan
docker compose build --no-cache rag-api
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ">>> Redémarrage rag-api..." -ForegroundColor Cyan
docker compose up -d rag-api
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Start-Sleep -Seconds 5
Write-Host ">>> Vérification routes /auth dans le conteneur..." -ForegroundColor Cyan
$check = docker exec rag-api python -c "
from api.main import app
paths = [getattr(r,'path',None) for r in app.routes]
auth = [p for p in paths if p and '/auth' in p]
print('AUTH_ROUTES:', len(auth))
for p in sorted(auth):
    print(' ', p)
" 2>&1
Write-Host $check

if ($check -notmatch "AUTH_ROUTES: [1-9]") {
    Write-Host "Les routes auth sont absentes — vérifiez les logs." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Swagger : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "OpenAPI : http://localhost:8000/openapi.json" -ForegroundColor Green
