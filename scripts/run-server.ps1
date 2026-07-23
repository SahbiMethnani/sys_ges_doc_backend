<#
.SYNOPSIS
  Lance le stack DocRAG complet via docker-compose à la racine PFE.

.EXAMPLE
  .\scripts\run-server.ps1
#>
param(
    [switch]$Kubernetes
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PfeRoot = (Resolve-Path (Join-Path $ProjectRoot "..")).Path

if ($Kubernetes) {
    & (Join-Path $PfeRoot "scripts\k8s-deploy.ps1") -BuildImages
    exit $LASTEXITCODE
}

Write-Host ">>> Démarrage via docker-compose racine PFE..." -ForegroundColor Cyan
Set-Location $PfeRoot
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Frontend  : http://localhost:4200" -ForegroundColor Green
Write-Host "API       : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Modèle LLM: .\scripts\pull-model.ps1" -ForegroundColor Yellow
