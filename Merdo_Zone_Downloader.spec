# -*- mode: python ; coding: utf-8 -*-
"""Windows release specification for Merdo Zone Downloader.

Requires vendor/bin/{deno,ffmpeg,ffprobe}.exe; prepare with scripts/prepare_tools.ps1.
Build mode is set by MERDO_BUILD_MODE=onedir|onefile in build_release.ps1.
"""
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH).resolve()
mode = os.environ.get('MERDO_BUILD_MODE', 'onedir').lower()
if mode not in ('onedir', 'onefile'):
    raise ValueError('MERDO_BUILD_MODE must be onedir or onefile')

required = ['deno.exe', 'ffmpeg.exe', 'ffprobe.exe']
tool_dir = root / 'vendor' / 'bin'
missing = [name for name in required if not (tool_dir / name).is_file()]
if missing:
    raise RuntimeError('Missing packaged tools: ' + ', '.join(missing)
                       + ' -- run scripts/prepare_tools.ps1 first')

# yt_dlp_ejs includes JavaScript/data files that a plain import scan may miss.
datas, extra_binaries, hiddenimports = collect_all('yt_dlp_ejs')
yt_datas, yt_binaries, yt_hidden = collect_all('yt_dlp')
datas += yt_datas + copy_metadata('yt-dlp') + copy_metadata('yt-dlp-ejs')
extra_binaries += yt_binaries
hiddenimports += yt_hidden
extra_binaries += [(str(tool_dir / name), 'tools') for name in required]

icon_file = root / 'assets' / 'merdo.ico'
icon_opts = {'icon': str(icon_file)} if icon_file.is_file() else {}

a = Analysis(
    [str(root / 'app' / 'merdo_zone_downloader.py')],
    pathex=[str(root / 'app')],
    binaries=extra_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)

if mode == 'onefile':
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name='Merdo_Zone_Downloader',
        debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        **icon_opts,
    )
else:
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name='Merdo_Zone_Downloader',
        debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        **icon_opts,
    )
    coll = COLLECT(
        exe, a.binaries, a.datas,
        strip=False, upx=False,
        name='Merdo_Zone_Downloader',
    )
