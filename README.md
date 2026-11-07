# Merdo Zone Downloader

A dark, turquoise-branded desktop download manager powered by **Python + PySide6 + yt-dlp**. Supports playlists, download quality, resume, skip existing files, progress/ETA, and download logs.

**Windows x64 release packaging** is included: an automated PowerShell build creates both a portable ZIP and an optional one-file EXE containing Python, PySide6, yt-dlp, yt-dlp-ejs, Deno, FFmpeg, and FFprobe.

## Build on Windows

Run `build_windows.bat`. For an offline alternative using your locally installed Deno/FFmpeg tools:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release.ps1 -Mode both -UseInstalledTools
```

Find release artifacts in `release/`. Do not commit binaries into Git history; publish them under GitHub **Releases**. A workflow is available in `.github/workflows/build-windows.yml`.

## Documentation

[Arabic build and publication guide](README_AR.md) · [Third-party notices](THIRD_PARTY_NOTICES.md) · [Application source](app/merdo_zone_downloader.py)

### Redistribution and licensing

This repo's original application code is offered under MIT (see LICENSE). Bundled dependencies have **separate** licensing obligations, notably Qt/PySide6 and FFmpeg. Review the notices and comply with the applicable terms *before publishing*. OneFile and static FFmpeg builds may require additional work for LGPL compliance. This project provides a build recipe, not a guarantee of complete license compliance.

Use only for media you are authorized to download. Server/network availability and site-side restrictions still apply.
