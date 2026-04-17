<#
.SYNOPSIS
  Lance l'API RAG (Docker Compose par défaut, ou Kubernetes + port-forward).

  Minikube : dans le meme terminal, avant -Kubernetes :
    minikube start
    minikube docker-env | Invoke-Expression   # puis relancer ce script

.EXAMPLE
  .\scripts\run-server.ps1
  .\scripts\run-server.ps1 -Kubernetes
#>
param(
    [switch]$Kubernetes
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

function Assert-DockerEngine {
    # Avec $ErrorActionPreference = Stop, stderr de "docker" declenche une exception :
    # on neutralise le temps du test.
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        & docker version 2>&1 | Out-Null
        $dockerOk = ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $saved
    }
    if (-not $dockerOk) {
        Write-Host ""
        Write-Host "Docker ne repond pas (moteur inaccessible ou Docker Desktop arrete)." -ForegroundColor Red
        Write-Host "1) Demarrez Docker Desktop et attendez l'icone baleine (pret)." -ForegroundColor Yellow
        Write-Host "2) Verifiez : docker version" -ForegroundColor Yellow
        Write-Host "3) Si vous utilisez WSL2 : Docker Desktop > Settings > Resources > WSL integration" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

Assert-DockerEngine

if ($Kubernetes) {
    Write-Host ">>> Construction de l'image rag-api:local ..." -ForegroundColor Cyan
    docker build -t rag-api:local $ProjectRoot

    Write-Host ">>> Application des manifests Kubernetes (dossier k8s/) ..." -ForegroundColor Cyan
    kubectl apply -f (Join-Path $ProjectRoot "k8s")

    Write-Host ">>> Attente du deploiement rag-api ..." -ForegroundColor Cyan
    kubectl rollout status deployment/rag-api --timeout=600s

    Write-Host ">>> Port-forward : http://localhost:8000 (CTRL+C pour arreter)" -ForegroundColor Green
    kubectl port-forward service/rag-api 8000:8000
}
else {
    Write-Host ">>> Demarrage avec Docker Compose (http://localhost:8000) ..." -ForegroundColor Cyan
    docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") up --build
}
