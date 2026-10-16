# Migra los datos de Pedrozilla 1.x (motor Chromium/Qt) a Firefox.
#
# Lee %APPDATA%\pedrozilla\bookmarks.json (lista de {title, url}) y genera
# un HTML en formato Netscape dentro del perfil, listo para importar desde
# Firefox: Biblioteca (Ctrl+Shift+O) > Importar y respaldar > Importar
# marcadores desde HTML.
#
# No modifica ni borra los datos originales. Si no hay nada que migrar,
# termina en silencio con codigo 0.
# (Sin acentos a proposito: PowerShell 5.1 lee los .ps1 en ANSI.)

param([string]$ProfileDir = "")

$ErrorActionPreference = "Stop"

if (-not $ProfileDir) {
    $base = $env:APPDATA
    if (-not $base) { $base = Join-Path $HOME "AppData\Roaming" }
    $ProfileDir = Join-Path $base "pedrozilla\firefox-profile"
}
$legacyDir = Split-Path -Parent $ProfileDir
$bookmarksJson = Join-Path $legacyDir "bookmarks.json"

if (-not (Test-Path $bookmarksJson)) {
    Write-Host "   (sin datos de Pedrozilla 1.x: no hay nada que migrar)"
    exit 0
}

try {
    $items = Get-Content $bookmarksJson -Raw | ConvertFrom-Json
} catch {
    Write-Host "   AVISO: no se pudo leer $bookmarksJson, se omite la migracion."
    exit 0
}
if (-not $items -or $items.Count -eq 0) {
    Write-Host "   (Pedrozilla 1.x no tenia marcadores)"
    exit 0
}

function Escape-Html([string]$text) {
    return [System.Net.WebUtility]::HtmlEncode($text)
}

$lines = @(
    '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    '<TITLE>Marcadores de Pedrozilla 1.x</TITLE>',
    '<H1>Marcadores de Pedrozilla 1.x</H1>',
    '<DL><p>'
)
foreach ($item in $items) {
    $url = [string]$item.url
    $title = [string]$item.title
    if (-not $url) { continue }
    if (-not $title) { $title = $url }
    $lines += '    <DT><A HREF="' + (Escape-Html $url) + '">' + (Escape-Html $title) + '</A>'
}
$lines += '</DL><p>'

New-Item -ItemType Directory -Force $ProfileDir | Out-Null
$target = Join-Path $ProfileDir "bookmarks-pedrozilla-1x.html"
$lines -join "`r`n" | Out-File $target -Encoding utf8

Write-Host ("   {0} marcadores exportados a:" -f $items.Count)
Write-Host "   $target"
Write-Host "   Importalos en Firefox: Ctrl+Shift+O > Importar y respaldar > Importar marcadores desde HTML."
