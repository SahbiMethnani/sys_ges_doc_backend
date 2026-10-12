# Démarre MySQL et OpenLDAP utilisés par l'API locale (Docker)
$ErrorActionPreference = "Stop"
$BackendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PfeRoot = (Resolve-Path (Join-Path $BackendRoot "..")).Path

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

Set-Location $PfeRoot
Write-Host ">>> Démarrage MySQL et OpenLDAP depuis le Compose racine..." -ForegroundColor Cyan
docker compose up -d --wait mysql openldap phpldapadmin
if ($LASTEXITCODE -ne 0) {
    Write-Host "Échec du démarrage de MySQL/OpenLDAP." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ">>> Initialisation de l'annuaire LDAP..." -ForegroundColor Cyan
docker compose run --rm ldap-seed
if ($LASTEXITCODE -ne 0) {
    Write-Host "Échec du seed LDAP." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "MySQL OK sur localhost:3306" -ForegroundColor Green
Write-Host "LDAP OK sur ldap://localhost:389" -ForegroundColor Green
Write-Host "Interface web : http://localhost:8081 (si phpLDAPadmin est démarré)" -ForegroundColor Green
Write-Host "  Login DN : cn=admin,dc=sysgesdoc,dc=local"
Write-Host "  Password : admin"
Write-Host "Application  : Sahbi / admin"
Write-Host ""
Write-Host "Lancez ensuite l'API locale depuis sys_gestion_doc et Angular depuis rag-frontend."
