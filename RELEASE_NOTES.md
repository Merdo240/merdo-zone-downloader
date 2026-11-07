# Merdo Zone Downloader v1.2.0

Windows x64 desktop app.

## Features
- Single video and playlist downloads
- Quality caps and container selection
- Resume partial downloads and skip existing files
- Progress, speed, ETA and activity log
- Bundled Python, PySide6, yt-dlp, yt-dlp-ejs, Deno, FFmpeg and FFprobe (when built through release scripts)

## Downloads
- **Portable ZIP** (recommended): extract the whole folder, run `Merdo_Zone_Downloader.exe`
- **OneFile EXE**: double-click `Merdo_Zone_Downloader_v1.2_Win64.exe`, first launch may be slower due to extraction

No separate Python/pip installation required for end users. Internet is still needed for media downloads. Some websites may restrict access; network/server errors may persist independently of packaging.

## Before shipping
Verify license redistribution obligations for Qt/PySide6, FFmpeg and other dependencies. Test the generated Windows release on a clean x64 machine. Read `THIRD_PARTY_NOTICES.md`.
