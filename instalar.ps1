# Instala Pedrozilla 2.x en Windows (distribucion basada en Firefox):
#   - prepara el perfil propio (%APPDATA%\pedrozilla\firefox-profile)
#   - migre los marcadores de Pedrozilla 1.x a un HTML importable (si existe)
#   - crea accesos directos en el Escritorio y en el menu Inicio
#
# No necesita Python ni administrador. Requiere Firefox instalado.
# (Sin acentos a proposito: PowerShell 5.1 lee los .ps1 en ANSI.)

$ErrorActionPreference = "Stop"

$ProjectDir = $PSScriptRoot
$DisplayName = "Pedrozilla"
$IconPath = Join-Path $ProjectDir "assets\pedrozilla.ico"
$base = $env:APPDATA
if (-not $base) { $base = Join-Path $HOME "AppData\Roaming" }
$ProfileDir = Join-Path $base "pedrozilla\firefox-profile"

function Find-Firefox {
    $candidates = @(
        (Join-Path $env:ProgramFiles "Mozilla Firefox\firefox.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Mozilla Firefox\firefox.exe")
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    $found = (Get-Command firefox -ErrorAction SilentlyContinue)
    if ($found) { return $found.Source }
    return $null
}

Write-Host "==> Buscando Firefox"
$firefox = Find-Firefox
if (-not $firefox) {
    Write-Host "ERROR: no se encontro Firefox. Instalalo desde:"
    Write-Host "  https://www.mozilla.org/firefox/"
    exit 1
}
Write-Host "   $firefox"

Write-Host "==> Preparando perfil"
& (Join-Path $ProjectDir "tools\init-profile.ps1") -ProfileDir $ProfileDir | Out-Null
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "==> Migrando marcadores de Pedrozilla 1.x (si existen)"
& (Join-Path $ProjectDir "tools\migrate-1x.ps1") -ProfileDir $ProfileDir

$iconOk = Test-Path $IconPath

Write-Host "==> Creando accesos directos"
$shell = New-Object -ComObject WScript.Shell

function New-PedrozillaShortcut {
    param([string]$Path, [string]$ExtraArguments = "")
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $firefox
    $shortcut.Arguments = '-profile "' + $ProfileDir + '"' + $ExtraArguments
    $shortcut.WorkingDirectory = $ProjectDir
    $shortcut.Description = "Navegador web basado en Firefox (Gecko)"
    if ($iconOk) { $shortcut.IconLocation = "$IconPath,0" }
    $shortcut.Save()
    Write-Host "   $Path"
}

$desktop = [Environment]::GetFolderPath("Desktop")
New-PedrozillaShortcut -Path (Join-Path $desktop "$DisplayName.lnk")
New-PedrozillaShortcut -Path (Join-Path $desktop "$DisplayName (privada).lnk") -ExtraArguments " -private-window"
New-PedrozillaShortcut -Path (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$DisplayName.lnk")

Write-Host ""
Write-Host "Listo. Tres formas de abrirlo:"
Write-Host ""
Write-Host '  1. Menu Inicio  ->  escribe "Pedrozilla"'
Write-Host "  2. Doble clic en el Escritorio  ->  Pedrozilla.lnk"
Write-Host '  3. Terminal  ->  "run.bat"  (o "run.bat --incognito")'
Write-Host ""
Write-Host "Proyecto: $ProjectDir"
Write-Host "Perfil:   $ProfileDir"
