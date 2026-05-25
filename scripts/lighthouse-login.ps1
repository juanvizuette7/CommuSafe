param(
    [string]$Url = "https://commusafe.onrender.com/login/"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$reportsDir = Join-Path $root "reports\lighthouse"

if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$outputPath = Join-Path $reportsDir "login-$timestamp.html"

Write-Host "Ejecutando Lighthouse para $Url"
Write-Host "Reporte: $outputPath"

& npx --yes lighthouse $Url `
    --output html `
    --output-path $outputPath `
    --chrome-flags="--disable-gpu"

$lighthouseExitCode = $LASTEXITCODE

if (Test-Path -LiteralPath $outputPath) {
    Write-Host "Abriendo reporte de estadisticas..."
    Start-Process -FilePath $outputPath

    if ($lighthouseExitCode -ne 0) {
        Write-Warning "Lighthouse termino con codigo $lighthouseExitCode, pero el reporte fue generado y abierto."
    }

    exit 0
}

Write-Error "Lighthouse no genero el reporte HTML."
exit $lighthouseExitCode
