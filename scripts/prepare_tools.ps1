param(
    [switch]$UseInstalled
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$target = Join-Path $root 'vendor\bin'
$cache = Join-Path $root '.cache\tools'
New-Item -ItemType Directory -Force -Path $target, $cache | Out-Null

function Download-Archive([string]$url, [string]$filename) {
    $archivePath = Join-Path $cache $filename
    if (-not (Test-Path $archivePath)) {
        Write-Host "Downloading $filename from official release source..." -ForegroundColor Cyan
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing
    }
    return $archivePath
}

function Verify-Archive([string]$archive, [string]$checksumUrl, [string]$assetName) {
    Write-Host "Verifying SHA256 for $assetName..." -ForegroundColor Cyan
    $checksumFile = Join-Path $cache (([IO.Path]::GetFileName($archive)) + '.sha256check')
    Invoke-WebRequest -Uri $checksumUrl -OutFile $checksumFile -UseBasicParsing
    $candidate = Get-Content $checksumFile | Where-Object { $_ -match [regex]::Escape($assetName) } | Select-Object -First 1
    if ($null -eq $candidate) { throw "Cannot find published checksum for $assetName" }
    if ($candidate -notmatch '([a-fA-F0-9]{64})') { throw "Invalid checksum entry for $assetName" }
    $expected = $Matches[1].ToLowerInvariant()
    $actual = (Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "SHA256 mismatch for $assetName. Aborting." }
    Write-Host "SHA256 verified: $assetName" -ForegroundColor Green
}

function Copy-LocalTool([string]$name) {
    $existing = Get-Command "$name.exe" -ErrorAction SilentlyContinue
    if ($null -eq $existing) {
        throw "$name.exe not found in PATH. Run without -UseInstalled to download official binaries."
    }
    $src = $existing.Source
    $dst = Join-Path $target "$name.exe"
    if ([IO.Path]::GetFullPath($src) -ne [IO.Path]::GetFullPath($dst)) {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    Write-Host "Using locally installed $name at $src" -ForegroundColor Cyan
}

if ($UseInstalled) {
    foreach ($name in @('deno', 'ffmpeg', 'ffprobe')) { Copy-LocalTool $name }
} else {
    # Official Deno release. Fixed version for repeatable builds.
    if (-not (Test-Path (Join-Path $target 'deno.exe'))) {
        $denoUrl = 'https://github.com/denoland/deno/releases/download/v2.9.7/deno-x86_64-pc-windows-msvc.zip'
        $denoZip = Download-Archive $denoUrl 'deno-2.9.7-win-x64.zip'
        Verify-Archive $denoZip ($denoUrl + '.sha256sum') 'deno-x86_64-pc-windows-msvc.zip'
        $denoExtract = Join-Path $cache 'deno_extract'
        Expand-Archive -LiteralPath $denoZip -DestinationPath $denoExtract -Force
        $denoExe = Get-ChildItem $denoExtract -Filter 'deno.exe' -File -Recurse | Select-Object -First 1
        if ($null -eq $denoExe) { throw 'deno.exe missing in downloaded Deno archive.' }
        Copy-Item $denoExe.FullName (Join-Path $target 'deno.exe') -Force
    }

    # Official BtbN Windows FFmpeg LGPL *static* build (no external FFmpeg DLLs).
    # The 'latest' release may update; see SHA256 manifest produced below.
    if (-not (Test-Path (Join-Path $target 'ffmpeg.exe')) -or
        -not (Test-Path (Join-Path $target 'ffprobe.exe'))) {
        $ffmpegUrl = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n8.1-latest-win64-lgpl-8.1.zip'
        $ffmpegZip = Download-Archive $ffmpegUrl 'ffmpeg-n8.1-lgpl-static-win-x64.zip'
        Verify-Archive $ffmpegZip 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/checksums.sha256' 'ffmpeg-n8.1-latest-win64-lgpl-8.1.zip'
        $ffmpegExtract = Join-Path $cache 'ffmpeg_extract'
        Expand-Archive -LiteralPath $ffmpegZip -DestinationPath $ffmpegExtract -Force
        foreach ($name in @('ffmpeg', 'ffprobe')) {
            $exe = Get-ChildItem $ffmpegExtract -Filter "$name.exe" -File -Recurse | Select-Object -First 1
            if ($null -eq $exe) { throw "$name.exe missing in downloaded FFmpeg archive." }
            Copy-Item $exe.FullName (Join-Path $target "$name.exe") -Force
        }
    }
}

$hashReport = Join-Path $root 'vendor\TOOLS_SHA256.txt'
$lines = @('# Bundled tool SHA256 hashes (verify original upstream releases before distribution)')
foreach ($name in @('deno.exe', 'ffmpeg.exe', 'ffprobe.exe')) {
    $path = Join-Path $target $name
    if (-not (Test-Path $path)) { throw "$name missing: $path" }
    $hash = (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToLowerInvariant()
    $lines += "$hash  $name"
    Write-Host "Prepared: $name" -ForegroundColor Green
}
$lines | Set-Content -Path $hashReport -Encoding UTF8
Write-Host "All tools prepared in $target" -ForegroundColor Green
Write-Host 'Verify third-party license obligations before publishing.' -ForegroundColor Yellow
