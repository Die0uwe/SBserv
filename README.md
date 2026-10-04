<p align="center"><img src="assets/logo_512.png" width="140" alt="SBserv logo"></p>

# SBserv

**Stand-alone web server + database. Easy to install, local and beyond.**
**Standalone webserver + database. Eenvoudig te installeren, lokaal en daarbuiten.**

SBserv is a portable web server for Windows with a built-in SQLite database, an automatic start page and an optional public link (Cloudflare Quick Tunnel). English and Dutch included; more languages can be added through a translation repository.

SBserv is een draagbare webserver voor Windows met ingebouwde SQLite-database, een automatische startpagina en een optionele publieke link (Cloudflare Quick Tunnel). Engels en Nederlands zijn ingebouwd; meer talen komen via een vertaal-repository.

## Features / Functies

| | EN | NL |
|---|---|---|
| Server | Local web server on `127.0.0.1`, free port picked automatically | Lokale webserver op `127.0.0.1`, vrije poort automatisch gekozen |
| Database | SQLite (`database.db`, WAL), logs table ready | SQLite (`database.db`, WAL), logs-tabel klaar |
| Public link | Cloudflare Quick Tunnel; `cloudflared` is bundled or downloaded and verified automatically | Cloudflare Quick Tunnel; `cloudflared` wordt meegeleverd of automatisch gedownload en gecontroleerd |
| Dashboard | Own resizable app window (Edge/Chrome app mode) on `127.0.0.1:8081`: status, tunnel on/off, files, database view, settings (port, language, text size) | Eigen verschaalbaar app-venster (Edge/Chrome app-modus) op `127.0.0.1:8081`: status, tunnel aan/uit, bestanden, database, instellingen (poort, taal, tekstgrootte) |
| Languages | EN / NL, switch in the menu (`[7]`), translations are JSON files | EN / NL, wisselen in het menu (`[7]`), vertalingen zijn JSON-bestanden |
| Start page | Logo, favicon and bilingual page in `public_html` (never overwrites your files) | Logo, favicon en tweetalige pagina in `public_html` (overschrijft nooit je bestanden) |
| Installer | Inno Setup, language choice EN/NL, no Python needed on the target PC | Inno Setup, taalkeuze EN/NL, geen Python nodig op de doel-pc |

## Quick start / Snel starten

```text
python sbserv.py            # needs Python 3.8+ / vereist Python 3.8+
python sbserv.py --lang nl  # force a language / taal forceren
```

Dashboard: opens automatically (`--no-browser` to skip) or press `D` in the menu / opent automatisch (`--no-browser` om over te slaan) of druk `D` in het menu.

Menu: `[1]` open site · `[2]` files · `[3]` public tunnel · `[4]` database logs · `[5]` change port · `[6]` stop tunnel · `[7]` language · `[8]` exit.

## Build the installer / Installer bouwen

Requirements / Vereist: Windows, Python 3, [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```bat
build.bat
```

This (1) installs PyInstaller, (2) builds `dist\sbserv.exe` with the logo as icon, (3) fetches `cloudflared.exe`, (4) compiles `sbserv_installer.iss` into `SBserv_Setup_v1.0.exe`.
Without `build.bat` the `.iss` falls back to `sbserv.py` (then Python must be installed on the PC).

## Translations / Vertalingen

Strings live in `assets/lang/<code>.json` (copy `en.json`, translate the values, keep the keys). The app also reads `lang/<code>.json` from the data folder and can fetch updates from a GitHub repository (`LANG_REPO` in `sbserv.py` or `"lang_repo"` in `config.json`). Expected layout: `lang/index.json` + `lang/<code>.json`.

## Project layout / Indeling

```text
sbserv.py               the application / de applicatie
sbserv_installer.iss    Inno Setup script
build.bat               exe + installer build
assets/                 logo, favicon, installer images, start page, lang/*.json
assets/dashboard.html   the dashboard UI / de dashboard-interface
examples/mockup.html    original design mockup / oorspronkelijke ontwerp-mockup
tests/                  python -m unittest discover -s tests -v
```

## Security notes / Beveiliging

* The dashboard runs on its own port (127.0.0.1 only, per-session token, Host check) and is never part of the tunnel.
* The server only listens on `127.0.0.1`; only the tunnel makes it reachable from outside, and only while you run it.
* Everything in `public_html` becomes public while the tunnel runs. Do not put secrets there.
* Downloaded translations are plain JSON text and are validated; no code is executed from them.
