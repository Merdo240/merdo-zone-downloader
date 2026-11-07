"""Merdo Zone Downloader — a desktop frontend for yt-dlp.

Dependencies: pip install PySide6 "yt-dlp[default]"
FFmpeg and Deno can be embedded in packaged Windows releases.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


# Locate FFmpeg and Deno both in a development checkout and in PyInstaller
# executables. In --onefile builds sys._MEIPASS is the temporary extraction folder.
def _candidate_tool_directories() -> list[Path]:
    locations = []
    if getattr(sys, 'frozen', False):
        locations.append(Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)) / 'tools')
        locations.append(Path(sys.executable).resolve().parent / 'tools')
    else:
        locations.append(Path(__file__).resolve().parent.parent / 'vendor' / 'bin')
    return locations


def find_tool(name: str) -> str | None:
    filename = name + ('.exe' if os.name == 'nt' else '')
    for directory in _candidate_tool_directories():
        found = directory / filename
        if found.is_file():
            return str(found)
    return shutil.which(name)


def enable_bundled_tools() -> None:
    # Some internal subprocesses rely on PATH instead of yt-dlp options.
    for directory in _candidate_tool_directories():
        if directory.is_dir():
            current = os.environ.get('PATH', '')
            os.environ['PATH'] = str(directory) + os.pathsep + current
            break


APP_NAME = 'Merdo Zone Downloader'
APP_VERSION = '1.2'
BG = '#010000'
SURFACE = '#0A1111'
SURFACE2 = '#0F1919'
BORDER = '#1D3332'
ACCENT = '#009F94'
ACCENT_LIGHT = '#23CCBD'
WHITE = '#F3FAF9'
MUTED = '#8BA3A0'
DIM = '#5A7471'


STYLESHEET = f"""
QWidget {{
    background: transparent;
    color: {WHITE};
    font-family: 'Segoe UI', 'Arial';
    font-size: 13px;
}}
QMainWindow, #root {{ background: {BG}; }}
QFrame#sidebar {{ background: #050B0B; border-right: 1px solid {BORDER}; }}
QFrame#surface {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 17px; }}
QFrame#subsurface {{ background: {SURFACE2}; border: 1px solid #203635; border-radius: 12px; }}
QFrame#logoTile {{ background: #09312E; border: 1px solid {ACCENT}; border-radius: 13px; }}
QFrame#statusTile {{ background: #071412; border: 1px solid #16413B; border-radius: 13px; }}
QFrame#divider {{ background: {BORDER}; max-height: 1px; min-height: 1px; }}
QLabel#eyebrow {{ color: {ACCENT_LIGHT}; font-size: 10px; font-weight: 700; letter-spacing: 2px; }}
QLabel#title {{ color: {WHITE}; font-size: 29px; font-weight: 800; }}
QLabel#cardHeading {{ color: {WHITE}; font-size: 17px; font-weight: 700; }}
QLabel#fieldHeading {{ color: #C7DCD9; font-size: 11px; font-weight: 700; }}
QLabel#muted {{ color: {MUTED}; font-size: 12px; }}
QLabel#dim {{ color: {DIM}; font-size: 11px; }}
QLabel#statNumber {{ color: {WHITE}; font-size: 30px; font-weight: 800; }}
QLabel#mono {{ color: #B8D5D1; font: 11px 'Consolas', monospace; }}
QLabel#brand {{ color: {WHITE}; font-size: 16px; font-weight: 800; letter-spacing: 1px; }}
QLabel#badge {{ color: {ACCENT_LIGHT}; background: #0C2A27; border: 1px solid #1C5A53; border-radius: 10px; padding: 6px 10px; font-size: 11px; font-weight: 700; }}
QLineEdit, QComboBox, QSpinBox {{
    min-height: 38px;
    background: {SURFACE2};
    color: {WHITE};
    border: 1px solid #29403D;
    border-radius: 9px;
    padding: 0 12px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT_LIGHT}; background: #122321; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {DIM}; background: #0B1212; }}
QComboBox::drop-down {{ border: none; width: 27px; }}
QComboBox QAbstractItemView {{
    background: #14201F; color: {WHITE}; border: 1px solid {BORDER};
    selection-background-color: #13544E; padding: 4px;
}}
QSpinBox::up-button, QSpinBox::down-button {{ border: none; width: 17px; background: transparent; }}
QPushButton {{ border: none; font-weight: 650; outline: none; }}
QPushButton#primary {{
    background: {ACCENT}; color: #001E1B; border-radius: 11px;
    padding: 12px 18px; font-size: 14px; font-weight: 800; min-height: 22px;
}}
QPushButton#primary:hover {{ background: {ACCENT_LIGHT}; }}
QPushButton#primary:disabled {{ background: #1C3835; color: #6E8783; }}
QPushButton#secondary {{
    background: #10201F; color: #CFDFDD; border: 1px solid #294542;
    border-radius: 9px; padding: 9px 14px; min-height: 20px;
}}
QPushButton#secondary:hover {{ background: #183A36; border-color: {ACCENT}; }}
QPushButton#secondary:disabled {{ background: #0B1515; color: #5A6F6C; border-color: #1A2D2A; }}
QPushButton#danger {{
    background: #281919; color: #F3A29D; border: 1px solid #673C3B;
    border-radius: 9px; padding: 9px 14px; min-height: 20px;
}}
QPushButton#danger:disabled {{ background: #181515; color: #806967; border-color: #302524; }}
QPushButton#choice {{
    text-align: left; color: {MUTED}; background: #0C1615; border: 1px solid #223936;
    border-radius: 10px; padding: 14px 16px; font-size: 12px;
}}
QPushButton#choice:checked {{
    color: {WHITE}; background: #0D2A27; border: 1px solid {ACCENT};
}}
QPushButton#choice:hover {{ border-color: #236F65; }}
QCheckBox {{ color: #CFDEDB; font-size: 12px; spacing: 9px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border-radius: 5px; border: 1px solid #3A5550; background: #10201D; }}
QCheckBox::indicator:checked {{ border-color: {ACCENT}; background: {ACCENT}; image: none; }}
QProgressBar {{ background: #10221F; border: 1px solid #1D3B36; border-radius: 7px; min-height: 11px; max-height: 11px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 6px; }}
QTextEdit {{ background: #060E0D; color: #B2D2CC; border: 1px solid #1E3330; border-radius: 11px; padding: 13px; font: 11px 'Consolas', monospace; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 1px; }}
QScrollBar::handle:vertical {{ background: #23423E; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
"""


def label(text: str, style: str = '', word_wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    if style:
        lbl.setObjectName(style)
    lbl.setWordWrap(word_wrap)
    return lbl


def panel() -> QFrame:
    frame = QFrame()
    frame.setObjectName('surface')
    return frame


def format_bytes(size: float | None) -> str:
    if not size:
        return '—'
    value = float(size)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if value < 1024 or unit == 'TB':
            return f'{value:.1f} {unit}'
        value /= 1024
    return '—'


def format_eta(seconds: Any) -> str:
    if seconds is None:
        return '—'
    seconds = max(0, int(seconds))
    if seconds >= 3600:
        return f'{seconds // 3600:d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'
    return f'{seconds // 60:02d}:{seconds % 60:02d}'


class ActivityStrip(QWidget):
    """Packet-style activity glyph, not a borrowed brand image."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(122, 40)
        self.phase = 0
        self.running = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)

    def set_running(self, running: bool):
        self.running = running
        if running:
            self.timer.start(170)
        else:
            self.timer.stop()
        self.update()

    def advance(self):
        self.phase += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        levels = [8, 13, 20, 12, 27, 19, 31, 15, 23, 11, 20, 13]
        for i, height in enumerate(levels):
            if self.running:
                height = min(32, height + (((self.phase + i * 3) % 5) - 2) * 3)
            active = i >= 5 if not self.running else (i + self.phase) % 4 != 0
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(ACCENT_LIGHT if active else '#22433D'))
            painter.drawRoundedRect(i * 10 + 2, int((40 - height) / 2), 5, height, 2, 2)
        painter.end()


@dataclass(frozen=True)
class DownloadConfig:
    url: str
    directory: str
    playlist: bool
    quality: str
    container: str
    prefer_compatible: bool
    skip_existing: bool
    start_index: int
    end_index: int


class DownloadWorker(QThread):
    progress_changed = Signal(object)
    activity = Signal(str, str)
    completed = Signal(str, str)

    def __init__(self, config: DownloadConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.config = config
        self.stop_requested = threading.Event()
        self.last_progress_emit = 0.0
        self.last_video = None
        self.seen_items: set[str] = set()
        self.started_count = 0

    def stop(self):
        self.stop_requested.set()

    def _check_stop(self):
        if self.stop_requested.is_set():
            raise DownloadCancelled('Download cancelled by user')

    def _progress_hook(self, data: dict):
        self._check_stop()
        info = data.get('info_dict') or {}
        video_id = str(info.get('id') or '')
        if video_id and video_id not in self.seen_items:
            self.seen_items.add(video_id)
            self.started_count += 1
        status = data.get('status', '')
        now = time.monotonic()
        if status == 'downloading' and now - self.last_progress_emit < 0.15:
            return
        self.last_progress_emit = now
        downloaded = data.get('downloaded_bytes') or 0
        total = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
        percent = min(100, downloaded / total * 100) if total else 0
        payload = {
            'status': status,
            'title': info.get('title') or Path(data.get('filename') or '').name or 'Current video',
            'percent': percent,
            'speed': data.get('speed'),
            'eta': data.get('eta'),
            'downloaded': downloaded,
            'total': total,
            'index': info.get('playlist_index'),
            'started_count': self.started_count,
        }
        self.progress_changed.emit(payload)
        if status == 'finished':
            self.activity.emit('Downloaded streams. Processing file…', 'info')

    def _postprocessor_hook(self, data: dict):
        self._check_stop()
        if data.get('status') == 'started':
            self.activity.emit('Merging or processing downloaded streams…', 'info')

    def _match_filter(self, info: dict, *, incomplete: bool = False):
        self._check_stop()
        return None

    def run(self):
        if yt_dlp is None:
            self.completed.emit('error', 'yt-dlp is not installed. Run pip install -r requirements.txt')
            return
        try:
            cfg = self.config
            os.makedirs(cfg.directory, exist_ok=True)
            outtmpl = (
                '%(playlist_index)s - %(title)s.%(ext)s'
                if cfg.playlist else '%(title)s.%(ext)s'
            )
            path_template = os.path.join(cfg.directory, outtmpl)
            if cfg.quality == 'Best available':
                fmt = 'bv+ba/b'
            else:
                height = int(cfg.quality.removesuffix('p'))
                fmt = f'bv[height<={height}]+ba/b[height<={height}]'

            opts: dict[str, Any] = {
                'format': fmt,
                'outtmpl': {'default': path_template},
                'noplaylist': not cfg.playlist,
                'continuedl': True,
                'overwrites': not cfg.skip_existing,
                'quiet': True,
                'no_warnings': False,
                'ignoreerrors': False,
                'progress_hooks': [self._progress_hook],
                'postprocessor_hooks': [self._postprocessor_hook],
                'match_filter': self._match_filter,
                'logger': WorkerLogger(self.activity),
                # Longer socket timeout and retries help with intermittent networks.
                # They do not guarantee recovery if the remote server is unavailable.
                'socket_timeout': 45,
                'retries': 12,
                'fragment_retries': 12,
                'extractor_retries': 5,
                'windowsfilenames': True,
                # yt-dlp EJS may need to fetch official challenge-solver scripts.
                # Downloads come from the official yt-dlp-ejs GitHub releases.
                'remote_components': {'ejs:github'},
            }
            # Prefer Deno but enable Node.js as a supported fallback.
            # If neither is installed, yt-dlp will report the missing runtime.
            runtimes = {}
            if find_tool('deno'):
                runtimes['deno'] = {'path': find_tool('deno')}
            if find_tool('node'):
                runtimes['node'] = {'path': find_tool('node')}
            if runtimes:
                opts['js_runtimes'] = runtimes
            if find_tool('ffmpeg'):
                opts['ffmpeg_location'] = str(Path(find_tool('ffmpeg')).parent)
            if cfg.skip_existing:
                # The archive also prevents repeat downloads across different
                # filenames or quality settings after this app has downloaded them.
                opts['download_archive'] = os.path.join(cfg.directory, '.merdo_download_archive.txt')
            if cfg.playlist:
                opts['playliststart'] = cfg.start_index
                if cfg.end_index > 0:
                    opts['playlistend'] = cfg.end_index
            if cfg.container != 'Auto':
                opts['merge_output_format'] = cfg.container.lower()
            if cfg.prefer_compatible:
                # Preference only; not a re-encode or guarantee of H.264/AAC.
                opts['format_sort'] = ['res', 'codec:avc:m4a']

            self.activity.emit('Connecting to source…', 'info')
            with yt_dlp.YoutubeDL(opts) as downloader:
                result = downloader.download([cfg.url])
            if self.stop_requested.is_set():
                self.completed.emit('cancelled', 'Download stopped. Partial files can be resumed later.')
            elif result == 0:
                self.completed.emit('success', 'Download completed successfully.')
            else:
                self.completed.emit('error', f'Download finished with code {result}. Check the log.')
        except DownloadCancelled:
            self.completed.emit('cancelled', 'Download stopped. Partial files can be resumed later.')
        except Exception as exc:
            if self.stop_requested.is_set():
                self.completed.emit('cancelled', 'Download stopped. Partial files can be resumed later.')
            else:
                self.completed.emit('error', f'{type(exc).__name__}: {exc}')


class DownloadCancelled(Exception):
    pass


class WorkerLogger:
    # Strip terminal colors such as [0;32m from the GUI activity log.
    ANSI_ESCAPE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

    def __init__(self, signal: Signal):
        self.signal = signal
        self.last_debug = None

    def debug(self, message):
        message = self.ANSI_ESCAPE.sub('', str(message))
        if message.startswith('[debug]'):
            return
        if ('[download]' in message or '[Merger]' in message) and message != self.last_debug:
            self.last_debug = message
            level = 'warning' if 'timed out' in message.lower() or 'retrying' in message.lower() else 'info'
            self.signal.emit(message, level)

    def warning(self, message):
        self.signal.emit(self.ANSI_ESCAPE.sub('', str(message)), 'warning')

    def error(self, message):
        self.signal.emit(self.ANSI_ESCAPE.sub('', str(message)), 'error')


class DownloaderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Merdo Zone — Downloader Studio')
        self.resize(1160, 825)
        self.setMinimumSize(890, 690)
        self.worker: DownloadWorker | None = None
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._update_playlist_options()
        self._set_running(False)
        QTimer.singleShot(200, self._prerequisite_note)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName('root')
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(246)
        outer.addWidget(sidebar)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(25, 30, 22, 27)
        side.setSpacing(15)

        logo_row = QHBoxLayout()
        logo_tile = QFrame()
        logo_tile.setObjectName('logoTile')
        logo_tile.setFixedSize(53, 53)
        logo_layout = QVBoxLayout(logo_tile)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_label = label('MZ')
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f'font: 800 20px "Segoe UI"; color: {ACCENT_LIGHT};')
        logo_layout.addWidget(logo_label)
        logo_row.addWidget(logo_tile)
        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        brand_col.addWidget(label('MERDO ZONE', 'brand'))
        brand_col.addWidget(label('SOFTWARE STUDIO', 'dim'))
        logo_row.addLayout(brand_col)
        logo_row.addStretch()
        side.addLayout(logo_row)
        side.addSpacing(36)
        side.addWidget(label('WORKSPACE', 'eyebrow'))

        item = QFrame()
        item.setObjectName('subsurface')
        il = QHBoxLayout(item)
        il.setContentsMargins(15, 13, 12, 13)
        il.addWidget(label('⬇', 'badge'))
        il.addWidget(label('Video downloader'))
        il.addStretch()
        side.addWidget(item)
        side.addSpacing(12)
        side.addWidget(label('ENGINE STATUS', 'eyebrow'))
        self.ytdlp_state = label('yt-dlp  /  checking…', 'muted')
        self.ffmpeg_state = label('FFmpeg  /  checking…', 'muted')
        self.js_state = label('JS runtime  /  checking…', 'muted')
        side.addWidget(self.ytdlp_state)
        side.addWidget(self.ffmpeg_state)
        side.addWidget(self.js_state)

        side.addStretch(1)
        note_box = QFrame()
        note_box.setObjectName('statusTile')
        nb = QVBoxLayout(note_box)
        nb.setContentsMargins(16, 17, 15, 17)
        nb.setSpacing(8)
        nb.addWidget(label('BUILT FOR LONG COURSES', 'eyebrow'))
        nb.addWidget(label('Resume partially downloaded files and skip completed lessons.', 'muted', True))
        side.addWidget(note_box)
        side.addSpacing(10)
        side.addWidget(label(f'MERDO ZONE  /  v{APP_VERSION}', 'dim'))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll, 1)
        content = QWidget()
        scroll.setWidget(content)
        main = QVBoxLayout(content)
        main.setContentsMargins(37, 31, 38, 28)
        main.setSpacing(21)
        self.main_layout = main

        heading = QHBoxLayout()
        hleft = QVBoxLayout()
        hleft.setSpacing(7)
        hleft.addWidget(label('MEDIA  /  DOWNLOAD ENGINE', 'eyebrow'))
        hleft.addWidget(label('Download smarter.', 'title'))
        hleft.addWidget(label('One workspace. Every lesson. Pick up where you left off.', 'muted'))
        heading.addLayout(hleft)
        heading.addStretch()
        self.activity_strip = ActivityStrip()
        heading.addWidget(self.activity_strip, alignment=Qt.AlignVCenter)
        main.addLayout(heading)

        self.setup_panel = panel()
        setup = QVBoxLayout(self.setup_panel)
        setup.setContentsMargins(23, 23, 23, 23)
        setup.setSpacing(17)
        top = QHBoxLayout()
        top.addWidget(label('New download', 'cardHeading'))
        top.addStretch()
        top.addWidget(label('01  /  SETUP', 'eyebrow'))
        setup.addLayout(top)

        setup.addWidget(label('VIDEO OR PLAYLIST LINK', 'fieldHeading'))
        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText('https://www.youtube.com/playlist?list=...')
        self.url_entry.setClearButtonEnabled(True)
        url_row.addWidget(self.url_entry, 1)
        self.paste_button = QPushButton('Paste link')
        self.paste_button.setObjectName('secondary')
        self.paste_button.clicked.connect(self._paste_url)
        url_row.addWidget(self.paste_button)
        setup.addLayout(url_row)

        setup.addWidget(label('DOWNLOAD MODE', 'fieldHeading'))
        type_row = QHBoxLayout()
        type_row.setSpacing(10)
        self.playlist_btn = QPushButton('▤   Full course / Playlist')
        self.single_btn = QPushButton('▶   Single video')
        for btn in (self.playlist_btn, self.single_btn):
            btn.setObjectName('choice')
            btn.setCheckable(True)
            btn.setMinimumHeight(57)
            type_row.addWidget(btn)
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        self.type_group.addButton(self.playlist_btn)
        self.type_group.addButton(self.single_btn)
        self.playlist_btn.setChecked(True)
        self.playlist_btn.toggled.connect(self._update_playlist_options)
        setup.addLayout(type_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(9)
        grid.addWidget(label('VIDEO QUALITY', 'fieldHeading'), 0, 0)
        grid.addWidget(label('OUTPUT CONTAINER', 'fieldHeading'), 0, 1)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['Best available', '1080p', '720p', '480p'])
        self.quality_combo.setCurrentText('720p')
        self.container_combo = QComboBox()
        self.container_combo.addItems(['Auto', 'MP4', 'MKV'])
        grid.addWidget(self.quality_combo, 1, 0)
        grid.addWidget(self.container_combo, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        setup.addLayout(grid)

        setup.addWidget(label('SAVE TO FOLDER', 'fieldHeading'))
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_entry = QLineEdit()
        self.path_entry.setText(str(Path.home() / 'Downloads' / 'Merdo Zone'))
        path_row.addWidget(self.path_entry, 1)
        browse = QPushButton('Browse…')
        browse.setObjectName('secondary')
        browse.clicked.connect(self._choose_folder)
        path_row.addWidget(browse)
        setup.addLayout(path_row)

        self.skip_cb = QCheckBox('Skip files already downloaded')
        self.skip_cb.setChecked(True)
        self.codec_cb = QCheckBox('Prefer widely compatible codecs (H.264 / AAC) when available')
        self.codec_cb.setChecked(True)
        setup.addWidget(self.skip_cb)
        setup.addWidget(self.codec_cb)

        self.range_frame = QFrame()
        self.range_frame.setObjectName('subsurface')
        range_layout = QHBoxLayout(self.range_frame)
        range_layout.setContentsMargins(15, 13, 15, 13)
        range_layout.setSpacing(14)
        range_layout.addWidget(label('PLAYLIST RANGE', 'eyebrow'))
        range_layout.addStretch()
        range_layout.addWidget(label('Start at', 'muted'))
        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, 1000000)
        self.start_spin.setValue(1)
        self.start_spin.setFixedWidth(87)
        range_layout.addWidget(self.start_spin)
        range_layout.addWidget(label('End at', 'muted'))
        self.end_spin = QSpinBox()
        self.end_spin.setRange(0, 1000000)
        self.end_spin.setSpecialValueText('All')
        self.end_spin.setFixedWidth(90)
        range_layout.addWidget(self.end_spin)
        setup.addWidget(self.range_frame)

        launch = QHBoxLayout()
        self.start_button = QPushButton('↓   Start download')
        self.start_button.setObjectName('primary')
        self.start_button.clicked.connect(self._begin)
        self.start_button.setMinimumWidth(194)
        launch.addWidget(self.start_button)
        self.stop_button = QPushButton('■   Stop')
        self.stop_button.setObjectName('danger')
        self.stop_button.clicked.connect(self._stop)
        launch.addWidget(self.stop_button)
        launch.addStretch()
        self.open_folder_btn = QPushButton('Open folder  ↗')
        self.open_folder_btn.setObjectName('secondary')
        self.open_folder_btn.clicked.connect(self._open_folder)
        launch.addWidget(self.open_folder_btn)
        setup.addLayout(launch)
        main.addWidget(self.setup_panel)

        progress_panel = panel()
        prog = QVBoxLayout(progress_panel)
        prog.setContentsMargins(23, 23, 23, 23)
        prog.setSpacing(14)
        ph = QHBoxLayout()
        ph.addWidget(label('Download activity', 'cardHeading'))
        ph.addStretch()
        self.status_label = label('READY', 'badge')
        ph.addWidget(self.status_label)
        prog.addLayout(ph)
        self.video_title = label('No active download', 'muted', True)
        prog.addWidget(self.video_title)
        pr = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        pr.addWidget(self.progress_bar, 1)
        self.percent_label = label('0%', 'mono')
        self.percent_label.setFixedWidth(44)
        self.percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pr.addWidget(self.percent_label)
        prog.addLayout(pr)
        metrics = QGridLayout()
        metrics.setSpacing(8)
        self.speed_label = label('—', 'statNumber')
        self.eta_label = label('—', 'statNumber')
        self.video_index_label = label('—', 'statNumber')
        for col, (value_label, caption) in enumerate([
            (self.speed_label, 'TRANSFER / SEC'),
            (self.eta_label, 'TIME REMAINING'),
            (self.video_index_label, 'PLAYLIST ITEM'),
        ]):
            value_label.setStyleSheet(f'color:{WHITE};font-size:21px;font-weight:750;')
            metrics.addWidget(value_label, 0, col)
            metrics.addWidget(label(caption, 'dim'), 1, col)
            metrics.setColumnStretch(col, 1)
        prog.addLayout(metrics)
        main.addWidget(progress_panel)

        log_panel = panel()
        log_content = QVBoxLayout(log_panel)
        log_content.setContentsMargins(23, 22, 23, 22)
        log_header = QHBoxLayout()
        log_header.addWidget(label('Activity log', 'cardHeading'))
        log_header.addStretch()
        clear_button = QPushButton('Clear')
        clear_button.setObjectName('secondary')
        clear_button.clicked.connect(lambda: self.log.clear())
        log_header.addWidget(clear_button)
        log_content.addLayout(log_header)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(130)
        self.log.setMaximumHeight(175)
        self.log.document().setMaximumBlockCount(250)
        log_content.addWidget(self.log)
        main.addWidget(log_panel)

        footer = QHBoxLayout()
        footer.addWidget(label('MERDO ZONE  —  BUILD • CREATE • SHIP', 'dim'))
        footer.addStretch()
        footer.addWidget(label('Powered by yt-dlp', 'dim'))
        main.addLayout(footer)
        main.addStretch()
        self._append_log('Studio ready. Bundled FFmpeg / Deno support enabled.', 'info')

    def _prerequisite_note(self):
        deno_found = bool(find_tool('deno'))
        node_found = bool(find_tool('node'))
        runtimes = ('Deno' if deno_found else '') + (' / ' if deno_found and node_found else '') + ('Node.js' if node_found else '')
        if runtimes:
            self.js_state.setText(f'●  JS runtime  /  {runtimes}')
        else:
            self.js_state.setText('●  JS runtime  /  NOT FOUND')
            self._append_log('YouTube needs Deno >= 2.3 or Node.js >= 22 for EJS challenges. Install one and restart the app.', 'warning')
        if yt_dlp:
            self.ytdlp_state.setText(f'●  yt-dlp  /  {yt_dlp.version.__version__}')
        else:
            self.ytdlp_state.setText('●  yt-dlp  /  NOT INSTALLED')
            self._append_log('yt-dlp is missing. Install requirements first.', 'error')
        if find_tool('ffmpeg'):
            self.ffmpeg_state.setText('●  FFmpeg  /  AVAILABLE')
        else:
            self.ffmpeg_state.setText('●  FFmpeg  /  NOT FOUND')
            self._append_log('FFmpeg not found on PATH. Separate audio/video streams may not merge.', 'warning')

    def _paste_url(self):
        self.url_entry.setText(QApplication.clipboard().text().strip())

    def _choose_folder(self):
        location = QFileDialog.getExistingDirectory(self, 'Select download folder', self.path_entry.text())
        if location:
            self.path_entry.setText(location)

    def _open_folder(self):
        folder = self.path_entry.text().strip().strip('"')
        if not folder:
            return
        Path(folder).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(Path(folder).resolve().as_uri())

    def _update_playlist_options(self):
        self.range_frame.setVisible(self.playlist_btn.isChecked())

    def _append_log(self, message: str, level: str = 'info'):
        from html import escape
        now = time.strftime('%H:%M:%S')
        color = {'info': '#9AC3BB', 'warning': '#E3BF7F', 'error': '#F1A19D', 'success': '#37D4C3'}.get(level, WHITE)
        self.log.append(f'<span style="color:#607F79">[{now}]</span> <span style="color:{color}">{escape(str(message))}</span>')

    def _set_running(self, running: bool):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.open_folder_btn.setEnabled(True)
        self.paste_button.setEnabled(not running)
        for widget in (self.url_entry, self.path_entry, self.quality_combo,
                       self.container_combo, self.skip_cb, self.codec_cb,
                       self.playlist_btn, self.single_btn, self.start_spin, self.end_spin):
            widget.setEnabled(not running)
        self.activity_strip.set_running(running)
        if running:
            self.status_label.setText('DOWNLOADING')
        elif self.status_label.text() == 'DOWNLOADING' or self.status_label.text() == 'STOPPING':
            self.status_label.setText('READY')

    def _begin(self):
        if self.worker is not None and self.worker.isRunning():
            return
        url = self.url_entry.text().strip()
        if not url.startswith(('https://', 'http://')):
            QMessageBox.warning(self, 'Invalid URL', 'Please enter a valid http(s) URL.')
            return
        directory = self.path_entry.text().strip().strip('"')
        if not directory:
            QMessageBox.warning(self, 'Missing folder', 'Choose a download folder first.')
            return
        if self.playlist_btn.isChecked() and self.end_spin.value() and self.end_spin.value() < self.start_spin.value():
            QMessageBox.warning(self, 'Invalid range', 'The final episode number must be greater than or equal to the starting number.')
            return
        if yt_dlp is None:
            QMessageBox.warning(self, 'Dependency missing', 'Install packages first: pip install -r requirements.txt')
            return
        if not find_tool('ffmpeg'):
            decision = QMessageBox.question(
                self, 'FFmpeg not found',
                'FFmpeg is not available on PATH. Video and audio may download separately without being merged. Continue anyway?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if decision != QMessageBox.Yes:
                return
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, 'Folder error', str(exc))
            return
        cfg = DownloadConfig(
            url=url,
            directory=directory,
            playlist=self.playlist_btn.isChecked(),
            quality=self.quality_combo.currentText(),
            container=self.container_combo.currentText(),
            prefer_compatible=self.codec_cb.isChecked(),
            skip_existing=self.skip_cb.isChecked(),
            start_index=self.start_spin.value(),
            end_index=self.end_spin.value(),
        )
        self.worker = DownloadWorker(cfg, self)
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.activity.connect(self._append_log)
        self.worker.completed.connect(self._on_completed)
        self.worker.finished.connect(self._on_thread_finished)
        self._set_running(True)
        self.progress_bar.setValue(0)
        self.percent_label.setText('0%')
        self.speed_label.setText('—')
        self.eta_label.setText('—')
        self.video_index_label.setText('—')
        self.video_title.setText('Connecting…')
        self._append_log(f'Started {"playlist" if cfg.playlist else "single video"} download.', 'success')
        if cfg.playlist:
            self._append_log(f'Playlist range: {cfg.start_index} to {cfg.end_index or "end"}.')
        self.worker.start()

    def _on_progress(self, data: dict):
        title = data.get('title') or 'Current video'
        if len(title) > 105:
            title = title[:102] + '...'
        self.video_title.setText(title)
        progress = float(data.get('percent', 0))
        self.progress_bar.setValue(round(progress * 10))
        self.percent_label.setText(f'{progress:.0f}%')
        speed = data.get('speed')
        self.speed_label.setText(f'{format_bytes(speed)}/s' if speed else '—')
        self.eta_label.setText(format_eta(data.get('eta')))
        index = data.get('index')
        self.video_index_label.setText(str(index if index is not None else data.get('started_count', '—')))
        if data.get('status') == 'finished':
            self.progress_bar.setValue(1000)
            self.percent_label.setText('100%')

    def _stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self.status_label.setText('STOPPING')
            self._append_log('Stop requested. Waiting for current operation to exit…', 'warning')

    def _on_completed(self, state: str, detail: str):
        state_label = {'success': 'COMPLETE', 'cancelled': 'STOPPED', 'error': 'ERROR'}.get(state, state.upper())
        self.status_label.setText(state_label)
        self._append_log(detail, 'success' if state == 'success' else 'warning' if state == 'cancelled' else 'error')
        if state == 'error':
            self.video_title.setText('Download failed. Check Activity log.')
        elif state == 'success':
            self.video_title.setText('All selected downloads are finished.')

    def _on_thread_finished(self):
        self._set_running(False)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, 'Download active', 'Stop the download first, then close the application.')
            event.ignore()
        else:
            event.accept()


def self_test() -> int:
    """CLI-free smoke test for packaged windowed EXEs; report is written to TEMP."""
    import subprocess
    import tempfile
    from importlib import metadata

    enable_bundled_tools()
    checks: list[str] = []
    errors: list[str] = []
    for package in ('yt-dlp', 'yt-dlp-ejs', 'PySide6'):
        try:
            checks.append(f'{package}: {metadata.version(package)}')
        except metadata.PackageNotFoundError:
            errors.append(f'Missing package: {package}')
    for tool in ('deno', 'ffmpeg', 'ffprobe'):
        location = find_tool(tool)
        if not location:
            errors.append(f'Missing tool: {tool}')
            continue
        try:
            proc = subprocess.run([location, '--version' if tool == 'deno' else '-version'],
                                  timeout=20, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, errors='replace')
            if proc.returncode != 0:
                errors.append(f'{tool} returned {proc.returncode}')
            else:
                checks.append(f'{tool}: {location}')
        except Exception as exc:
            errors.append(f'{tool}: {exc}')
    report = Path(tempfile.gettempdir()) / 'merdo_zone_downloader_self_test.txt'
    report.write_text('Merdo Zone Downloader self-test\n' + '\n'.join(checks + errors)
                      + '\n' + ('PASS' if not errors else 'FAIL') + '\n', encoding='utf-8')
    return 0 if not errors else 1


def main() -> int:
    if '--self-test' in sys.argv:
        return self_test()
    enable_bundled_tools()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))
    window = DownloaderWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
