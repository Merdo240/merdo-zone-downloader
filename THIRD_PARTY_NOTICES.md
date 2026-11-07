# Third-party components and redistribution

This app's MIT license applies **only to Merdo Zone's original application code**.
It does not replace the separate licenses of bundled third-party components.

- **PySide6 / Qt**: commonly supplied under LGPLv3 (or alternative GPL/commercial licensing). See https://doc.qt.io/qtforpython-6/ and https://www.qt.io/licensing . Review LGPLv3 requirements, including access to applicable licenses/source and users' ability to modify/replace LGPL-covered libraries. A **single-file self-extracting EXE** may entail extra compliance considerations compared with the portable folder build. This notice alone is **not** a guarantee of legal compliance.
- **FFmpeg**: depends on build configuration. The builder downloads BtbN's `win64-lgpl` static build, intended as an LGPL variant, but review `ffmpeg -version` / upstream build licenses and supply applicable notices, corresponding source/offers, and other LGPL compliance materials. https://ffmpeg.org/legal.html and https://github.com/BtbN/FFmpeg-Builds . Static linkage may trigger additional LGPL requirements.
- **Deno**: MIT; see https://github.com/denoland/deno/blob/main/LICENSE.md .
- **yt-dlp**: Unlicense; see https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE .
- **yt-dlp-ejs**: package includes scripts and transitive materials under respective licenses; see https://github.com/yt-dlp/ejs .
- **PyInstaller**: GPLv2 with special exception for generated applications; see https://pyinstaller.org/en/stable/license.html .

**Before distributing**: include the required license texts and source availability / compliance materials for the specific exact versions bundled. The portable ZIP includes this document as an initial notice, not a complete compliance package. Consider using an appropriate LGPL-compliant distribution approach and obtaining legal review before publication.

Windows may show a SmartScreen warning for unsigned binaries. Code-signing is recommended for public distribution, and binaries from CI should be scanned and tested.
