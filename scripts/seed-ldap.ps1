# Crée l'OU users et l'utilisateur Sahbi dans OpenLDAP (après démarrage du conteneur)
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Bootstrap = Join-Path $ProjectRoot "ldap\bootstrap"
$Container = "docrag-ldap"
$AdminDn = "cn=admin,dc=sysgesdoc,dc=local"
$AdminPw = "admin"

function Wait-LdapReady {
    param([int]$MaxAttempts = 30)
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        $running = docker inspect -f "{{.State.Running}}" $Container 2>$null
        if ($running -ne "true") {
            Start-Sleep -Seconds 2
            continue
        }
        docker exec $Container ldapsearch -x -H ldap://localhost -b "dc=sysgesdoc,dc=local" `
            -D $AdminDn -w $AdminPw -s base "(objectclass=*)" dn 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Import-LdifFile {
    param([string]$LocalPath)
    if (-not (Test-Path $LocalPath)) {
        throw "Fichier introuvable : $LocalPath"
    }
    # LF obligatoire : les LDIF Windows (CRLF) échouent silencieusement dans ldapadd
    $ldif = [System.IO.File]::ReadAllText($LocalPath) -replace "`r`n", "`n"
    if (-not $ldif.EndsWith("`n")) {
        $ldif += "`n"
    }

    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = $ldif | docker exec -i $Container ldapadd -x -H ldap://localhost `
        -D $AdminDn -w $AdminPw -c 2>&1
    $ErrorActionPreference = $prevEap
    $text = ($output | Out-String).Trim()
    $code = $LASTEXITCODE

    if ($code -eq 0) {
        Write-Host "  OK $(Split-Path $LocalPath -Leaf)" -ForegroundColor Green
        if ($text -match "adding new entry") { Write-Host "    $text" }
        return
    }
    if ($code -eq 68 -or $text -match "Already exists|already exists|\(68\)") {
        Write-Host "  Déjà présent : $(Split-Path $LocalPath -Leaf)" -ForegroundColor Yellow
        return
    }
    if ($text) { Write-Host $text }
    throw "ldapadd a échoué pour $(Split-Path $LocalPath -Leaf) (code $code)"
}

if (-not (Wait-LdapReady)) {
    Write-Host "LDAP non prêt. Vérifiez : docker logs $Container" -ForegroundColor Red
    exit 1
}

Write-Host ">>> Import des utilisateurs LDAP..." -ForegroundColor Cyan
Import-LdifFile (Join-Path $Bootstrap "01-ou-users.ldif")
Import-LdifFile (Join-Path $Bootstrap "02-user-sahbi.ldif")
Write-Host ">>> Seed LDAP terminé." -ForegroundColor Green
