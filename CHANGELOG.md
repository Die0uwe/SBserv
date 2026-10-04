# Changelog

## 1.1.0 - 2026-10-04
### Added
- Users and login (SQLite): `users` and `sessions` tables, scrypt password hashes with random salt (PBKDF2 fallback), session cookie (HttpOnly, SameSite=Lax, Secure over https), login lock-out (5 failures / 5 min per username and IP), CSRF check, optional self-registration (off by default).
- Public login API: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `POST /api/auth/register`.
- Dashboard: *Users* screen (add, set password, disable, delete, allow registration); EN/NL strings (147 keys each).
- Example page `login.html` (EN/NL) placed in `public_html` without overwriting.
- Database view hides the `sessions` table and masks `pw_hash`.
- 10 new tests (24 in total).

## 1.0.0 - 2026-10-04
First release of SBserv (grown out of the earlier "play_assistant" prototype).

### Added
- Installer script accepts an existing `sbserv.exe` (next to the `.iss` or in `dist\`), logo on all shortcuts, version info; `installer.bat` builds only the installer; GitHub Actions workflow builds exe + installer on Windows.
- Verified on Windows: PyInstaller exe runs, port change works, tunnel link created (using an existing `cloudflared`). Auto-download still to be tested on a PC without it.
- Original logo kept in `assets/source/`; `tools/make_images.py` regenerates logo, favicon (multi-size .ico) and installer images. Mockup is now one self-contained file (logo and favicon embedded).
- Dashboard: separate local admin server with API + resizable app window (status, tunnel start/stop with clear errors, website files, read-only database view, settings: port/language/text size). Protected by a per-session token and Host check; not reachable through the tunnel.
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
