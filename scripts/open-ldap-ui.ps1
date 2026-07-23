# Ouvre l'interface web phpLDAPadmin dans le navigateur (démarre les services si besoin)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& (Join-Path $PSScriptRoot "start-ldap.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Start-Sleep -Seconds 2
$url = "http://localhost:8081"

Write-Host ""
Write-Host "Interface LDAP : $url" -ForegroundColor Green
Write-Host ""
Write-Host "Connexion phpLDAPadmin :" -ForegroundColor Cyan
Write-Host "  Login DN : cn=admin,dc=sysgesdoc,dc=local"
Write-Host "  Password : admin"
Write-Host ""
Write-Host "Arborescence : dc=sysgesdoc,dc=local > ou=users > uid=Sahbi"
Write-Host ""

Start-Process $url
