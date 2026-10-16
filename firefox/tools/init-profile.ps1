# Prepara el perfil Firefox de Pedrozilla sin tocar el perfil normal de Firefox.
#
#   - Crea %APPDATA%\pedrozilla\firefox-profile (o la ruta de -ProfileDir).
#   - Copia user.js desde la plantilla (solo si no existe).
#   - Copia chrome\userChrome.css y la pagina local de nueva pestana.
#   - Lee el motor de busqueda heredado de Pedrozilla 1.x (settings.json)
#     y lo aplica al user.js recien creado.
#
# Es idempotente: nunca sobrescribe un user.js existente.
# (Sin acentos a proposito: PowerShell 5.1 lee los .ps1 en ANSI.)

param(
    [string]$ProfileDir = "",
    [string]$SkeletonDir = "",
    [string]$NewTabSource = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProfileDir -or -not $SkeletonDir -or -not $NewTabSource) {
    $toolsDir = $PSScriptRoot
    $projectDir = Split-Path -Parent $toolsDir
    if (-not $ProfileDir) {
        $base = $env:APPDATA
        if (-not $base) { $base = Join-Path $HOME "AppData\Roaming" }
        $ProfileDir = Join-Path $base "pedrozilla\firefox-profile"
    }
    if (-not $SkeletonDir) { $SkeletonDir = Join-Path $projectDir "firefox-profile-skeleton" }
    if (-not $NewTabSource) { $NewTabSource = Join-Path $projectDir "newtab\index.html" }
}

if (-not (Test-Path (Join-Path $SkeletonDir "user.js"))) {
    Write-Host "ERROR: no existe la plantilla $SkeletonDir\user.js"
    exit 1
}
if (-not (Test-Path $NewTabSource)) {
    Write-Host "ERROR: no existe la pagina $NewTabSource"
    exit 1
}

New-Item -ItemType Directory -Force $ProfileDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $ProfileDir "chrome") | Out-Null

# Pagina local de nueva pestana (copia del proyecto al perfil).
$newTabTarget = Join-Path $ProfileDir "pedrozilla-newtab.html"
Copy-Item $NewTabSource $newTabTarget -Force

# Tema clasico (sobrescribir es seguro: el usuario no lo edita a mano).
Copy-Item (Join-Path $SkeletonDir "chrome\userChrome.css") (Join-Path $ProfileDir "chrome\userChrome.css") -Force

# user.js: solo se crea, nunca se sobrescribe.
$userJs = Join-Path $ProfileDir "user.js"
if (-not (Test-Path $userJs)) {
    $fileUrl = "file:///" + ($newTabTarget -replace "\\", "/" -replace " ", "%20")
    $template = Get-Content (Join-Path $SkeletonDir "user.js") -Raw
    $template = $template.Replace("__PEDROZILLA_NEWTAB_URL__", $fileUrl)

    # Motor de busqueda heredado de Pedrozilla 1.x (si existe).
    $legacySettings = Join-Path (Split-Path -Parent $ProfileDir) "settings.json"
    $engine = ""
    if (Test-Path $legacySettings) {
        try {
            $parsed = Get-Content $legacySettings -Raw | ConvertFrom-Json
            $engine = [string]$parsed.search_engine
        } catch { $engine = "" }
    }
    $map = @{
        "duckduckgo" = "DuckDuckGo"; "google" = "Google"; "brave" = "Brave";
        "bing" = "Bing"; "ecosia" = "Ecosia"; "wikipedia" = "Wikipedia"; "youtube" = "YouTube"
    }
    if ($engine -and $map.ContainsKey($engine)) {
        $name = $map[$engine]
        $template = $template.Replace('"DuckDuckGo"', ('"' + $name + '"'))
    }

    $template | Out-File $userJs -Encoding utf8
    Write-Host "   perfil creado en $ProfileDir"
} else {
    Write-Host "   perfil ya existente en $ProfileDir"
}

Write-Output $ProfileDir
