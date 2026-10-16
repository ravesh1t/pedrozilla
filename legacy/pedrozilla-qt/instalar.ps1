# Instala Pedrozilla en Windows:
#   - icono .ico dentro de la carpeta del paquete
#   - acceso directo en el Escritorio y en el menu Inicio
#
# Si existe la aplicacion empaquetada (dist\Pedrozilla\Pedrozilla.exe), los
# accesos directos apuntan a ella y no hace falta Python para usarla.
#
# Vuelve a ejecutarlo cada vez que muevas la carpeta del proyecto.
#
# (Este archivo se mantiene sin acentos a proposito: PowerShell 5.1 lee los .ps1
#  en la codificacion ANSI del sistema y los acentos se verian mal.)

$ErrorActionPreference = "Stop"

$PackageDir = $PSScriptRoot
$ProjectDir = Split-Path -Parent $PackageDir
$DisplayName = "Pedrozilla"
$IconPath = Join-Path $PackageDir "pedrozilla.ico"
$AppExe = Join-Path $ProjectDir "dist\Pedrozilla\Pedrozilla.exe"

function Invoke-Native {
    # Ejecuta un programa externo sin que PowerShell interprete su salida de
    # error como un error terminante. Devuelve la salida y deja el codigo en
    # $LASTEXITCODE.
    param([string]$Exe, [string[]]$Arguments)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Exe @Arguments 2>&1
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Get-Interpreter {
    # Devuelve la ruta real de python.exe, o $null si el comando no existe o es
    # el alias vacio de la Microsoft Store.
    param([string]$Command)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) { return $null }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $line = (& $Command -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1)
    } finally {
        $ErrorActionPreference = $previous
    }
    if (-not $line) { return $null }
    $path = "$line".Trim()
    if ($path -and (Test-Path $path)) { return $path }
    return $null
}

function Get-PythonCandidates {
    $found = New-Object System.Collections.Generic.List[string]
    foreach ($command in @("py", "python")) {
        $path = Get-Interpreter $command
        if ($path) { $found.Add($path) }
    }
    foreach ($pattern in @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "$env:ProgramFiles\Python*\python.exe"
    )) {
        $items = @(Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
        foreach ($item in $items) { $found.Add($item.FullName) }
    }
    return @($found | Select-Object -Unique)
}

function Test-HasWebEngine {
    param([string]$Exe)
    Invoke-Native $Exe @("-c", "import PySide6.QtWebEngineWidgets") > $null
    return ($LASTEXITCODE -eq 0)
}

Write-Host "==> Comprobando dependencias"

$python = $null
foreach ($candidate in @(Get-PythonCandidates)) {
    if (Test-HasWebEngine $candidate) { $python = $candidate; break }
}

$hasApp = Test-Path $AppExe
if (-not $python -and -not $hasApp) {
    Write-Host "ERROR: no se encontro Python con PySide6. Instalalo con:"
    Write-Host "  python -m pip install PySide6"
    exit 1
}
if ($python) { Write-Host "   usando $python" }
if ($hasApp) { Write-Host "   aplicacion empaquetada: $AppExe" }

# -- icono -----------------------------------------------------------------
$iconOk = Test-Path $IconPath
if ($python) {
    Write-Host "==> Generando icono"
    $iconScript = @'
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
app = QApplication(["pedrozilla-icon"])

project, target = sys.argv[1], sys.argv[2]
sys.path.insert(0, project)
from pedrozilla.browser import brand_icon

icon = brand_icon(256)
sys.exit(0 if icon.pixmap(256, 256).save(target, "ICO") else 2)
'@

    $savedPlatform = $env:QT_QPA_PLATFORM
    $env:QT_QPA_PLATFORM = "offscreen"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $iconScript | & $python - $ProjectDir $IconPath
    $iconExit = $LASTEXITCODE
    $ErrorActionPreference = $previous
    $iconOk = ($iconExit -eq 0) -and (Test-Path $IconPath)
    if ($savedPlatform) {
        $env:QT_QPA_PLATFORM = $savedPlatform
    } else {
        Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    }

    if ($iconOk) {
        Write-Host "   icono guardado en $IconPath"
    } else {
        Write-Host "   AVISO: no se pudo generar el icono; se usara el generico."
    }
} else {
    Write-Host "==> Sin Python: se reutiliza el icono existente"
}

# -- destino de los accesos directos --------------------------------------
if ($hasApp) {
    $target = $AppExe
    $baseArgs = @()
    $workingDir = Split-Path -Parent $AppExe
} else {
    $target = Join-Path (Split-Path -Parent $python) "pythonw.exe"
    if (-not (Test-Path $target)) { $target = $python }
    $baseArgs = @("-m", "pedrozilla")
    $workingDir = $ProjectDir
}

Write-Host "==> Creando accesos directos"
$shell = New-Object -ComObject WScript.Shell

function New-PedrozillaShortcut {
    param([string]$Path, [string[]]$ExtraArguments = @())
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $target
    $shortcut.Arguments = ($baseArgs + $ExtraArguments) -join " "
    $shortcut.WorkingDirectory = $workingDir
    $shortcut.Description = "Navegador web basado en Chromium (Qt WebEngine)"
    if ($iconOk) { $shortcut.IconLocation = "$IconPath,0" }
    $shortcut.Save()
    Write-Host "   $Path"
}

$desktop = [Environment]::GetFolderPath("Desktop")
New-PedrozillaShortcut -Path (Join-Path $desktop "$DisplayName.lnk")
New-PedrozillaShortcut -Path (Join-Path $desktop "$DisplayName (privada).lnk") -ExtraArguments @("--incognito")
New-PedrozillaShortcut -Path (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$DisplayName.lnk")

Write-Host ""
Write-Host "Listo. Tres formas de abrirlo:"
Write-Host ""
Write-Host "  1. Menu Inicio  ->  escribe `"$DisplayName`""
Write-Host "  2. Doble clic en el Escritorio  ->  $DisplayName.lnk"
Write-Host "  3. Terminal  ->  `"$PackageDir\run.bat`""
Write-Host ""
Write-Host "Proyecto: $ProjectDir"
