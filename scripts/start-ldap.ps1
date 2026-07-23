# Démarre le serveur LDAP local (OpenLDAP via Docker)
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
    Write-Host "Docker Desktop n'est pas démarré. Lancez-le puis réessayez." -ForegroundColor Red
    exit 1
}

Write-Host ">>> Démarrage OpenLDAP + interface web..." -ForegroundColor Cyan
docker compose up -d openldap phpldapadmin
if ($LASTEXITCODE -ne 0) {
    Write-Host "Échec du démarrage LDAP." -ForegroundColor Red
    exit $LASTEXITCODE
}

Start-Sleep -Seconds 5
$running = docker ps --filter "name=sys-ges-doc-ldap" --filter "status=running" --format "{{.Names}}"
if (-not $running) {
    Write-Host "Le conteneur LDAP s'est arrêté. Logs :" -ForegroundColor Red
    docker logs sys-ges-doc-ldap 2>&1 | Select-Object -Last 30
    exit 1
}

& (Join-Path $PSScriptRoot "seed-ldap.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "LDAP OK sur ldap://localhost:389" -ForegroundColor Green
Write-Host "Interface web : http://localhost:8081  (phpLDAPadmin)" -ForegroundColor Green
Write-Host "  Login DN : cn=admin,dc=sysgesdoc,dc=local"
Write-Host "  Password : admin"
Write-Host "Application  : Sahbi / admin"
Write-Host ""
Write-Host "Ouvrir l'interface : .\scripts\open-ldap-ui.ps1"
Write-Host ""
