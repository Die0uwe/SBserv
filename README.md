<p align="center"><img src="assets/logo_512.png" width="140" alt="SBserv logo"></p>

# SBserv

**Stand-alone web server + database. Easy to install, local and beyond.**
**Standalone webserver + database. Eenvoudig te installeren, lokaal en daarbuiten.**

SBserv is a portable web server for Windows with a built-in SQLite database, an automatic start page and an optional public link (Cloudflare Quick Tunnel). English and Dutch included; more languages can be added through a translation repository.

SBserv is een draagbare webserver voor Windows met ingebouwde SQLite-database, een automatische startpagina en een optionele publieke link (Cloudflare Quick Tunnel). Engels en Nederlands zijn ingebouwd; meer talen komen via een vertaal-repository.

## Status / Stand van zaken (v1.1)

| | EN | NL |
|---|---|---|
| Works on Windows | `sbserv.exe` (PyInstaller) starts, serves the site, keeps its SQLite database, and a Cloudflare Quick Tunnel link was created (with a `cloudflared` already present on the PC) | `sbserv.exe` (PyInstaller) start, toont de site, bewaart de SQLite-database en een Cloudflare Quick Tunnel-link is aangemaakt (met een `cloudflared` die al op de pc stond) |
| Installer | `SBserv_Setup_v1.1.exe` built with Inno Setup | `SBserv_Setup_v1.1.exe` gebouwd met Inno Setup |
| Still to test | Automatic `cloudflared` download on a PC without it, installer in both languages on a clean PC, dashboard window on Windows, GitHub Actions build | Automatische `cloudflared`-download op een pc zonder, installer in beide talen op een schone pc, dashboard-venster op Windows, GitHub Actions-build |
| New in 1.1 | Users + login: `users` table (scrypt-hashed passwords), login API for your site, user management in the dashboard, example `login.html` (tested with unit tests, not yet on Windows) | Gebruikers + inloggen: `users`-tabel (wachtwoorden met scrypt), inlog-API voor je site, gebruikersbeheer in het dashboard, voorbeeld `login.html` (met unittests getest, nog niet op Windows) |
| Planned | Translation repository; optional fixed tunnel address | Vertaal-repository; optioneel vast tunneladres |

## Features / Functies

| | EN | NL |
|---|---|---|
| Server | Local web server on `127.0.0.1`, free port picked automatically | Lokale webserver op `127.0.0.1`, vrije poort automatisch gekozen |
| Database | SQLite (`database.db`, WAL), logs table ready | SQLite (`database.db`, WAL), logs-tabel klaar |
| Public link | Cloudflare Quick Tunnel; `cloudflared` is bundled or downloaded and verified automatically | Cloudflare Quick Tunnel; `cloudflared` wordt meegeleverd of automatisch gedownload en gecontroleerd |
| Dashboard | Own resizable app window (Edge/Chrome app mode) on `127.0.0.1:8081`: status, tunnel on/off, files, database view, settings (port, language, text size) | Eigen verschaalbaar app-venster (Edge/Chrome app-modus) op `127.0.0.1:8081`: status, tunnel aan/uit, bestanden, database, instellingen (poort, taal, tekstgrootte) |
| Users & login | SQLite `users` table, passwords hashed with scrypt (random salt), sessions in an HttpOnly cookie, lock-out after 5 failed attempts, optional self-registration (off by default). Manage users in the dashboard. | SQLite `users`-tabel, wachtwoorden met scrypt (willekeurige salt), sessies in een HttpOnly-cookie, blokkade na 5 foute pogingen, optioneel zelf registreren (standaard uit). Beheer gebruikers in het dashboard. |
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

## How the tunnel works / Hoe de tunnel werkt

EN: `cloudflared` opens an **outgoing** connection to Cloudflare and your local site (`127.0.0.1`) hangs behind a random `*.trycloudflare.com` link. No router ports, no account, no inbound firewall rule; outbound port 7844 must be allowed. Quick Tunnels are meant for testing: no uptime guarantee, max. 200 simultaneous requests, no server-sent events, and the link changes on every start. Your PC and SBserv must stay running. For a fixed address you need a Cloudflare account and your own domain (planned as an option).

NL: `cloudflared` maakt een **uitgaande** verbinding naar Cloudflare en je lokale site (`127.0.0.1`) hangt achter een willekeurige `*.trycloudflare.com`-link. Geen router-poorten, geen account, geen inkomende firewallregel; uitgaand poort 7844 moet open staan. Quick Tunnels zijn bedoeld om te testen: geen uptimegarantie, maximaal 200 gelijktijdige verzoeken, geen server-sent events en de link verandert bij elke start. Je pc en SBserv moeten blijven draaien. Voor een vast adres heb je een Cloudflare-account en een eigen domein nodig (gepland als optie).

Sources / Bronnen: [Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/), [Tunnel firewall](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/)

## Get the latest version / De nieuwste versie ophalen

Download the newest ZIP: https://github.com/Die0uwe/SBserv/archive/refs/heads/main.zip
De nieuwste ZIP downloaden: zie link hierboven.

## Build the installer / Installer bouwen

**Option A - on your PC / Optie A - op je eigen pc.** Requirements / Vereist: Windows, Python 3 (tick "Add to PATH"), [Inno Setup 6](https://jrsoftware.org/isinfo.php).
Unzip, then double-click / Uitpakken en dubbelklikken op:

```bat
build.bat
```

This (1) installs PyInstaller, (2) builds `dist\sbserv.exe` with the logo as icon, (3) fetches `cloudflared.exe`, (4) compiles `sbserv_installer.iss` into `SBserv_Setup_v1.1.exe`.
Without `build.bat` the `.iss` falls back to `sbserv.py` (then Python must be installed on the PC).

**Already have `sbserv.exe`? / Heb je al een `sbserv.exe`?** Put it next to `sbserv_installer.iss` (or in `dist\`), open the `.iss` in Inno Setup and press Ctrl+F9, or double-click `installer.bat`. / Zet hem naast `sbserv_installer.iss` (of in `dist\`), open de `.iss` in Inno Setup en druk Ctrl+F9, of dubbelklik `installer.bat`.

**Option B - nothing to install / Optie B - niets installeren.** GitHub builds it for you: *Actions > Build installer > Run workflow*, then download the `SBserv-installer` artifact. Pushing a tag like `v1.0.0` also publishes it as a Release.

## Users and login / Gebruikers en inloggen

EN: add users in the dashboard (*Users*). Your own pages talk to the public server (same port as the site, so it also works through the tunnel). All calls are JSON:

| Call | What it does |
|---|---|
| `POST /api/auth/login` `{"username","password"}` | signs in, sets the `sbserv_session` cookie (HttpOnly, SameSite=Lax, 7 days; `Secure` over the tunnel) |
| `GET /api/auth/me` | `200 {"ok":true,"user":"name"}` or `401` |
| `POST /api/auth/logout` | ends the session |
| `POST /api/auth/register` | only when enabled in the dashboard |

`login.html` in your website folder is a working example. Pages that must be private need a check on `/api/auth/me`; static files in `public_html` stay public. Usernames: 3-32 characters (letters, digits, `_ . -`, not case-sensitive); passwords 8-128 characters. The dashboard never shows password hashes and hides the `sessions` table. Over plain `http://localhost` the cookie is not `Secure`; through the tunnel (https) it is.

NL: voeg gebruikers toe in het dashboard (*Gebruikers*). Je eigen pagina's praten met de publieke server (zelfde poort als de site, dus het werkt ook via de tunnel). Alle aanroepen zijn JSON; zie de tabel hierboven. `login.html` in je websitemap is een werkend voorbeeld. Pagina's die privé moeten zijn, controleren `/api/auth/me`; statische bestanden in `public_html` blijven openbaar. Gebruikersnaam: 3-32 tekens (letters, cijfers, `_ . -`, niet hoofdlettergevoelig); wachtwoord 8-128 tekens. Het dashboard toont nooit wachtwoord-hashes en verbergt de tabel `sessions`.

## Translations / Vertalingen

Strings live in `assets/lang/<code>.json` (copy `en.json`, translate the values, keep the keys). The app also reads `lang/<code>.json` from the data folder and can fetch updates from a GitHub repository (`LANG_REPO` in `sbserv.py` or `"lang_repo"` in `config.json`). Expected layout: `lang/index.json` + `lang/<code>.json`.

## Project layout / Indeling

```text
sbserv.py               the application / de applicatie
sbserv_installer.iss    Inno Setup script (logo, EN/NL, shortcuts) / Inno Setup-script
build.bat               exe + cloudflared + installer in one go / alles in één keer
installer.bat           installer only, from an existing sbserv.exe / alleen de installer
assets/                 logo, favicon, installer images, start page, dashboard.html, lang/*.json
assets/source/          original logo (source of all icons) / originele logo (bron van alle iconen)
tools/make_images.py    regenerates logo, favicon and installer images / maakt alle afbeeldingen opnieuw
examples/mockup.html    design mockup, single self-contained file / ontwerp-mockup
tests/                  python -m unittest discover -s tests -v
.github/workflows/      build.yml - Windows build of exe + installer on GitHub
```

Build output is **not** in Git / Bouwresultaten staan **niet** in Git: `dist/`, `build/`, `*.spec`, `cloudflared.exe`, `SBserv_Setup_*.exe`, `*.zip`.

## Working from the folder / Werken vanuit de map

EN: the project folder on the PC (`C:\SERVERS\DIEOUWE-AI\SBwebserv`) is the working copy; GitHub (`Die0uwe/SBserv`, branch `main`) is kept identical for all tracked files. Run `python -m unittest discover -s tests` before pushing.

NL: de projectmap op de pc (`C:\SERVERS\DIEOUWE-AI\SBwebserv`) is de werkkopie; GitHub (`Die0uwe/SBserv`, branch `main`) wordt voor alle bijgehouden bestanden gelijk gehouden. Draai `python -m unittest discover -s tests` voor het pushen.

## Security notes / Beveiliging

* The dashboard runs on its own port (127.0.0.1 only, per-session token, Host check) and is never part of the tunnel.
* The server only listens on `127.0.0.1`; only the tunnel makes it reachable from outside, and only while you run it.
* Login: passwords are never stored in plain text; failed logins are throttled per username and per IP; POSTs must be JSON from the same origin (CSRF); wrong password and unknown user give the same answer. Use the tunnel (https) for real logins, not plain http over the internet.
* Everything in `public_html` becomes public while the tunnel runs. Do not put secrets there.
* Downloaded translations are plain JSON text and are validated; no code is executed from them.
