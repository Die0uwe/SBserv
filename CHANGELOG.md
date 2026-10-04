# Changelog

## 1.0.0 - 2026-10-04
First release of SBserv (grown out of the earlier "play_assistant" prototype).

### Added
- Local web server (127.0.0.1, threaded, automatic free-port fallback, clean restart on port change).
- SQLite database with WAL and event log.
- Cloudflare Quick Tunnel: bundled or auto-downloaded and validated `cloudflared`, internet check, 40 s timeout, stop option, clean shutdown, link copied to clipboard.
- Languages: English and Dutch, language menu, installer language choice passed to the app (`--lang`), online translation updates from a GitHub repo (`LANG_REPO`).
- Logo, favicon and bilingual start page; installer wizard images (multi-DPI).
- `build.bat` (PyInstaller exe + cloudflared + installer), unit tests, HTML dashboard mockup (`examples/mockup.html`).

### Fixed (compared with the prototype)
- Installer referenced a non-existent language file (`Dutchduc.isl`); now `Dutch.isl`.
- Changing the port left the old server running.
- Data was lost/unwritable when the install folder was read-only (falls back to `%LOCALAPPDATA%\SBserv`).
- Python is no longer required on the target PC when the exe is built.
