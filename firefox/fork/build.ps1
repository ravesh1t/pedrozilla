# Compila Pedrozilla (fork de Firefox) en Windows.
#
# Fases:
#   1. Comprueba Visual Studio 2022 (lo instala con winget si falta; pide admin).
#   2. Ejecuta "mach bootstrap" (MozillaBuild, Rust, Node; interactivo la 1a vez).
#   3. Copia mozconfig + branding al fuente.
#   4. Ejecuta "mach build" y "mach package".
#
# El fuente NO vive en este repo (pesa GBs): se descarga aparte a D:\mozilla
# (ver fork/README.md). La compilacion completa tarda horas.
# (Sin acentos a proposito: PowerShell 5.1 lee los .ps1 en ANSI.)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceDir = "D:\mozilla\firefox-156.0.1"
$ObjDir = Join-Path $SourceDir "obj-pedrozilla"

function Find-FirefoxSource {
    if (Test-Path (Join-Path $SourceDir "browser\branding\official")) { return $SourceDir }
    $found = Get-ChildItem "D:\mozilla" -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName "browser\branding\official") } |
        Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

Write-Host "==> Comprobando Visual Studio 2022"
$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$hasVs = $false
if (Test-Path $vsWhere) {
    $out = & $vsWhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools -property installationPath 2>$null
    if ($out) { $hasVs = $true; Write-Host "   $out" }
}
if (-not $hasVs) {
    Write-Host "   Instalando Visual Studio 2022 Community con winget (puede tardar)..."
    winget install --silent --accept-source-agreements --accept-package-agreements Microsoft.VisualStudio.2022.Community
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: fallo winget."; exit 1 }
}

Write-Host "==> Localizando fuente de Firefox"
$src = Find-FirefoxSource
if (-not $src) {
    Write-Host "ERROR: no hay fuente en D:\mozilla (ver fork/README.md, paso 1)."
    exit 1
}
Write-Host "   $src"

Write-Host "==> Copiando mozconfig y branding"
Copy-Item (Join-Path $RepoRoot "fork\mozconfig") (Join-Path $src "mozconfig") -Force
$brandTarget = Join-Path $src "browser\branding\pedrozilla"
New-Item -ItemType Directory -Force $brandTarget | Out-Null
Copy-Item (Join-Path $RepoRoot "fork\branding\pedrozilla\*") $brandTarget -Recurse -Force

Write-Host "==> mach bootstrap (solo la primera vez; puede pedir opciones)"
Write-Host "    Cuando pregunte, elige: Firefox for Desktop / Firefox."
& "$src\mach" bootstrap --application-choice browser
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: fallo bootstrap."; exit 1 }

Write-Host "==> mach build (tarda horas; no cierres esta ventana)"
& "$src\mach" build
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: fallo la compilacion (ver log)."; exit 1 }

Write-Host "==> mach package"
& "$src\mach" package
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: fallo el empaquetado."; exit 1 }

Write-Host ""
Write-Host "Listo. Binarios en: $ObjDir"
Write-Host "El instalador/zip queda en $ObjDir\dist o similar (ver log de package)."
