param(
    [ValidateSet('both', 'portable', 'onefile')]
    [string]$Mode = 'both',
    [switch]$UseInstalledTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

function Run-Checked([string]$exe, [string[]]$arguments) {
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $exe $($arguments -join ' ')" }
}

Write-Host 'Merdo Zone Downloader - Windows release build' -ForegroundColor Cyan
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    $py = (Get-Command python -ErrorAction Stop).Source
    Run-Checked $py @('-m', 'venv', '.venv')
}
Run-Checked $venvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'requirements-build.txt')

$prepare = Join-Path $PSScriptRoot 'prepare_tools.ps1'
& $prepare -UseInstalled:$UseInstalledTools
if (-not $?) { throw 'Tool preparation failed.' }

New-Item -ItemType Directory -Path (Join-Path $root 'release') -Force | Out-Null
$modes = if ($Mode -eq 'both') { @('onedir', 'onefile') } elseif ($Mode -eq 'portable') { @('onedir') } else { @('onefile') }

foreach ($buildMode in $modes) {
    $env:MERDO_BUILD_MODE = $buildMode
    Write-Host "Building $buildMode..." -ForegroundColor Cyan
    Run-Checked $venvPython @(
        '-m', 'PyInstaller',
        '--noconfirm', '--clean',
        '--distpath', (Join-Path $root "dist\$buildMode"),
        '--workpath', (Join-Path $root "build\$buildMode"),
        'Merdo_Zone_Downloader.spec'
    )

    if ($buildMode -eq 'onedir') {
        $folder = Join-Path $root 'dist\onedir\Merdo_Zone_Downloader'
        if (-not (Test-Path (Join-Path $folder 'Merdo_Zone_Downloader.exe'))) {
            throw 'Portable EXE not found after building.'
        }
        Copy-Item (Join-Path $root 'THIRD_PARTY_NOTICES.md') $folder -Force
        Copy-Item (Join-Path $root 'LICENSE') $folder -Force
        Copy-Item (Join-Path $root 'README_AR.md') $folder -Force
        $zip = Join-Path $root 'release\Merdo_Zone_Downloader_v1.2_Portable_Win64.zip'
        if (Test-Path $zip) { Remove-Item $zip -Force }
        Compress-Archive -Path $folder -DestinationPath $zip -CompressionLevel Optimal
        Write-Host "Portable ZIP: $zip" -ForegroundColor Green
    } else {
        $exe = Join-Path $root 'dist\onefile\Merdo_Zone_Downloader.exe'
        if (-not (Test-Path $exe)) { throw 'OneFile EXE not found after building.' }
        $dest = Join-Path $root 'release\Merdo_Zone_Downloader_v1.2_Win64.exe'
        Copy-Item $exe $dest -Force
        Write-Host "OneFile EXE: $dest" -ForegroundColor Green
    }
}

$releaseDir = Join-Path $root 'release'
$releaseFiles = Get-ChildItem $releaseDir -File | Where-Object { $_.Extension -in @('.zip', '.exe') }
$hashFile = Join-Path $releaseDir 'SHA256SUMS.txt'
$hashes = foreach ($item in $releaseFiles) {
    "$((Get-FileHash $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant())  $($item.Name)"
}
$hashes | Set-Content -Path $hashFile -Encoding UTF8
Copy-Item (Join-Path $root 'THIRD_PARTY_NOTICES.md') $releaseDir -Force
Write-Host "Build finished. Release assets: $releaseDir" -ForegroundColor Green
Write-Host 'Test on a clean Windows 10/11 PC before publishing.' -ForegroundColor Yellow
