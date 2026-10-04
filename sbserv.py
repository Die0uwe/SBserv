"""
SBserv 1.0
==========
Standalone, draagbare webserver met SQLite-database voor Windows.
Eenvoudig te installeren (Inno Setup) en met een optionele publieke link via een
Cloudflare Quick Tunnel.

* Lokale webserver (alleen 127.0.0.1) met automatische poortkeuze.
* SQLite-database (database.db, WAL) voor logs en eigen projecten.
* Cloudflare Quick Tunnel: cloudflared wordt gevonden of automatisch (en gecontroleerd)
  gedownload; internetcheck, timeout, stoppen en opruimen zijn ingebouwd.
* Meertalig (Engels/Nederlands) met taalkeuze in het menu; vertalingen zijn losse
  JSON-bestanden (assets/lang/*.json) die online bijgewerkt kunnen worden vanuit een
  eigen GitHub-repo (LANG_REPO).
* Logo, favicon en startpagina worden automatisch in public_html geplaatst.
* Werkt als .py en als PyInstaller-.exe (geen Python nodig bij gebruikers); data staat in
  een schrijfbare map (valt terug op %LOCALAPPDATA%\\SBserv).
"""

import http.server
import json
import locale
import os
import re
import shutil
import socket
import socketserver
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

APP_NAME = "SBserv"
APP_VERSION = "1.0"
DEFAULT_PORT = 8080
HOST = "127.0.0.1"
DIRECTORY = "public_html"
DB_NAME = "database.db"
CONFIG_NAME = "config.json"

# Officiele cloudflared releases (GitHub, door Cloudflare zelf gepubliceerd)
CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
CLOUDFLARED_MIN_BYTES = 10 * 1024 * 1024  # echte exe is ~60 MB; filtert HTML-foutpagina's
TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
TUNNEL_TIMEOUT = 40  # seconden wachten op een publieke URL

# Vertalingen: losse JSON-bestanden. Online updates komen uit een eigen GitHub-repo
# met /lang/index.json + /lang/<code>.json (zie assets/lang/ als voorbeeld).
# Pas LANG_REPO aan (of zet "lang_repo" in config.json) zodra de repo bestaat.
LANG_REPO = "Die0uwe/sbserv-lang"
LANG_BRANCH = "main"
LANG_CODE_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})?$")
LANG_NAME_MAP = {"dutch": "nl", "english": "en"}  # Inno Setup taalnamen


# ----------------------------------------------------------------------------
# Paden: app-map (waar de .exe/.py staat) en data-map (schrijfbaar)
# ----------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _is_writable(path):
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def _data_dir():
    app = _app_dir()
    if _is_writable(app):
        return app
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    fallback = os.path.join(base, "SBserv")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _resource_dirs():
    dirs = []
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        dirs.append(os.path.join(sys._MEIPASS, "assets"))
    dirs.append(os.path.join(_app_dir(), "assets"))
    return dirs


def resource_path(*parts):
    """Zoek een meegeleverd bestand (PyInstaller-bundel of assets-map)."""
    for d in _resource_dirs():
        p = os.path.join(d, *parts)
        if os.path.exists(p):
            return p
    return None


APP_DIR = _app_dir()
DATA_DIR = _data_dir()
WEB_ROOT = os.path.join(DATA_DIR, DIRECTORY)
DB_PATH = os.path.join(DATA_DIR, DB_NAME)
CONFIG_PATH = os.path.join(DATA_DIR, CONFIG_NAME)
BIN_DIR = os.path.join(DATA_DIR, "bin")
USER_LANG_DIR = os.path.join(DATA_DIR, "lang")
CF_NAME = "cloudflared.exe" if os.name == "nt" else "cloudflared"


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if isinstance(cfg, dict):
                return cfg
    except (OSError, ValueError):
        pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


# ----------------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def db_init():
    with db_connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS logs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, "
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )


def db_log(message):
    """Log een gebeurtenis; mag nooit de app laten crashen."""
    try:
        with db_connect() as conn:
            conn.execute("INSERT INTO logs (message) VALUES (?)", (message,))
    except sqlite3.Error:
        pass


def check_db_status():
    try:
        if not os.path.exists(DB_PATH):
            return False
        conn = db_connect()
        conn.execute("SELECT 1")
        conn.close()
        return True
    except sqlite3.Error:
        return False


# ----------------------------------------------------------------------------
# Startpagina
# ----------------------------------------------------------------------------
FALLBACK_INDEX = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'><title>SBserv</title>"
    "<link rel='icon' href='favicon.ico'></head><body style='font-family:sans-serif;background:#071526;"
    "color:#e2e8f0;padding:40px'><h1>SBserv</h1>"
    "<p>Put your files in <code>public_html</code> / Plaats je bestanden in <code>public_html</code>.</p>"
    "</body></html>"
)
WEB_ASSETS = ("index.html", "logo.png", "logo_512.png", "favicon.ico", "favicon-32.png", "apple-touch-icon.png")


def setup_environment():
    os.makedirs(WEB_ROOT, exist_ok=True)
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(USER_LANG_DIR, exist_ok=True)
    # Startpagina, logo en favicon: nooit bestaand werk van de gebruiker overschrijven
    for name in WEB_ASSETS:
        dest = os.path.join(WEB_ROOT, name)
        if os.path.exists(dest):
            continue
        src = resource_path(name)
        try:
            if src:
                shutil.copyfile(src, dest)
            elif name == "index.html":
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(FALLBACK_INDEX)
        except OSError:
            pass
    db_init()
    db_log("SBserv environment check completed.")


# ----------------------------------------------------------------------------
# Vertalingen (i18n)
# ----------------------------------------------------------------------------
class I18n:
    """Laadt Engels als basis en legt de gekozen taal eroverheen.
    Zoekvolgorde per taal: meegeleverd (assets/lang) -> gebruikersmap (data/lang, ook online updates).
    Ontbrekende of kapotte vertalingen vallen stil terug op Engels."""

    def __init__(self):
        self.code = "en"
        self.base = {}
        self.cur = {}

    @staticmethod
    def _read(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _load_code(self, code):
        merged = {}
        bundled = resource_path("lang", code + ".json")
        if bundled:
            merged.update(self._read(bundled))
        merged.update(self._read(os.path.join(USER_LANG_DIR, code + ".json")))
        return merged

    def available(self):
        """{code: native naam} van alle gevonden talen."""
        found = {}
        dirs = [os.path.join(d, "lang") for d in _resource_dirs()] + [USER_LANG_DIR]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for fn in os.listdir(d):
                code = fn[:-5]
                if fn.endswith(".json") and fn != "index.json" and LANG_CODE_RE.match(code):
                    meta = self._read(os.path.join(d, fn)).get("_meta", {})
                    found[code] = meta.get("native") or meta.get("name") or code
        found.setdefault("en", "English")
        return dict(sorted(found.items(), key=lambda kv: (kv[0] != "en", kv[0])))

    def set(self, code):
        if not self.base:
            self.base = self._load_code("en")
        self.code = code if LANG_CODE_RE.match(code or "") else "en"
        self.cur = self._load_code(self.code) if self.code != "en" else {}

    def __call__(self, key, **kw):
        text = self.cur.get(key) or self.base.get(key) or key
        try:
            return text.format(**kw)
        except (KeyError, IndexError, ValueError):
            try:  # kapotte vertaling -> Engels
                return (self.base.get(key) or key).format(**kw)
            except (KeyError, IndexError, ValueError):
                return text


t = I18n()


def detect_system_language():
    try:
        if os.name == "nt":
            import ctypes
            buf = ctypes.create_unicode_buffer(85)
            if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85):
                return buf.value.split("-")[0].lower()
        loc = (os.environ.get("LC_ALL") or os.environ.get("LANG") or locale.setlocale(locale.LC_CTYPE) or "")
        return loc.split("_")[0].split(".")[0].lower()
    except Exception:
        return "en"


def pick_initial_language(cfg):
    """--lang <code|dutch|english> (van de installer) > config.json > systeemtaal > en."""
    arg = None
    if "--lang" in sys.argv:
        i = sys.argv.index("--lang")
        if i + 1 < len(sys.argv):
            arg = sys.argv[i + 1].lower()
    arg = LANG_NAME_MAP.get(arg, arg)
    avail = t.available()
    for cand in (cfg.get("language") if not arg else arg, cfg.get("language"), detect_system_language()):
        if cand in avail:
            return cand
    return "en"


def update_translations(cfg):
    """Haal nieuwe/bijgewerkte vertalingen uit de GitHub-repo. Geeft aantal bijgewerkte bestanden terug."""
    repo = cfg.get("lang_repo") or LANG_REPO
    base = f"https://raw.githubusercontent.com/{repo}/{LANG_BRANCH}/lang/"
    headers = {"User-Agent": "SBserv/" + APP_VERSION}

    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:
            return r.read(512 * 1024)

    print(t("lang_upd_start", repo=repo))
    if not has_internet():
        print(t("lang_upd_none"))
        return 0
    try:
        index = json.loads(get(base + "index.json").decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(t("lang_upd_none") if e.code == 404 else t("lang_upd_fail", err=e))
        return 0
    except (urllib.error.URLError, socket.timeout, OSError, ValueError) as e:
        print(t("lang_upd_fail", err=e))
        return 0

    updated = 0
    for item in index.get("languages", []) if isinstance(index, dict) else []:
        code, fn = str(item.get("code", "")), str(item.get("file", ""))
        # Alleen platte, veilige bestandsnamen: geen paden, geen code - alleen tekst (JSON)
        if not LANG_CODE_RE.match(code) or fn != code + ".json":
            continue
        try:
            raw = get(base + fn)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict) or not all(isinstance(v, (str, dict)) for v in data.values()):
                continue
            dest = os.path.join(USER_LANG_DIR, fn)
            with open(dest + ".part", "wb") as f:
                f.write(raw)
            os.replace(dest + ".part", dest)
            updated += 1
        except (urllib.error.URLError, socket.timeout, OSError, ValueError):
            continue
    print(t("lang_upd_done", n=updated))
    return updated


# ----------------------------------------------------------------------------
# Webserver (beheerd, herstartbaar)
# ----------------------------------------------------------------------------
class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def log_message(self, format, *args):  # terminal schoon houden
        return


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class WebServer:
    def __init__(self):
        self.httpd = None
        self.thread = None
        self.port = None

    def start(self, port):
        self.stop()
        self.httpd = _Server((HOST, port), _Handler)
        self.port = port
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except OSError:
                pass
        self.httpd = None
        self.thread = None

    def is_running(self):
        """Echte check: antwoordt de server op HTTP?"""
        if not self.httpd or not self.port:
            return False
        try:
            urllib.request.urlopen(f"http://{HOST}:{self.port}", timeout=1).close()
            return True
        except (urllib.error.URLError, socket.timeout, OSError):
            return False


def port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, port))
            return True
        except OSError:
            return False


def find_free_port(preferred, tries=50):
    for p in range(preferred, min(preferred + tries, 65535)):
        if port_is_free(p):
            return p
    return None


# ----------------------------------------------------------------------------
# cloudflared: vinden / downloaden / valideren
# ----------------------------------------------------------------------------
def has_internet(timeout=4):
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            socket.create_connection((host, port), timeout=timeout).close()
            return True
        except OSError:
            continue
    return False


def _cf_works(path):
    """Is dit echt een werkende cloudflared? (voert --version uit)"""
    try:
        r = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=15,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return r.returncode == 0 and "cloudflared" in (r.stdout + r.stderr).lower()
    except (OSError, subprocess.SubprocessError):
        return False


def find_cloudflared():
    """Zoekvolgorde: meegeleverd naast de app -> data/bin -> PATH."""
    candidates = [
        os.path.join(APP_DIR, CF_NAME),
        os.path.join(BIN_DIR, CF_NAME),
        shutil.which("cloudflared"),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and _cf_works(c):
            return c
    return None


def download_cloudflared(retries=3):
    """Download de officiele cloudflared. Geeft pad terug of None."""
    if os.name != "nt":
        print(t("cf_win_only"))
        return None
    if not has_internet():
        print(t("cf_no_internet"))
        return None

    os.makedirs(BIN_DIR, exist_ok=True)
    target = os.path.join(BIN_DIR, CF_NAME)
    part = target + ".part"

    for attempt in range(1, retries + 1):
        try:
            print(t("cf_attempt", n=attempt, total=retries))
            req = urllib.request.Request(CLOUDFLARED_URL, headers={"User-Agent": "SBserv/" + APP_VERSION})
            with urllib.request.urlopen(req, timeout=30) as resp, open(part, "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r    {done * 100 // total:3d}%  ({done // 1024 // 1024} MB)", end="", flush=True)
            print()

            size = os.path.getsize(part)
            with open(part, "rb") as f:
                magic = f.read(2)
            if size < CLOUDFLARED_MIN_BYTES or magic != b"MZ":
                raise ValueError(t("cf_invalid", size=size))

            os.replace(part, target)  # atomisch: nooit een half bestand
            if not _cf_works(target):
                os.remove(target)
                raise ValueError(t("cf_wont_start"))

            db_log("cloudflared downloaded and validated.")
            print(t("cf_ok"))
            return target
        except (urllib.error.URLError, socket.timeout, OSError, ValueError) as e:
            print("\n" + t("cf_fail", err=e))
            for p in (part,):
                try:
                    os.remove(p)
                except OSError:
                    pass
            time.sleep(2 * attempt)

    print(t("cf_manual", name=CF_NAME, dir=BIN_DIR))
    return None


def ensure_cloudflared():
    path = find_cloudflared()
    if path:
        return path
    print(t("cf_missing"))
    return download_cloudflared()


# ----------------------------------------------------------------------------
# Tunnel (beheerd proces)
# ----------------------------------------------------------------------------
class Tunnel:
    def __init__(self):
        self.proc = None
        self.url = None
        self._lock = threading.Lock()

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, port):
        if self.is_running():
            return self.url
        cf = ensure_cloudflared()
        if not cf:
            return None
        if not has_internet():
            print(t("no_internet"))
            return None

        print(t("tunnel_starting"))
        try:
            self.proc = subprocess.Popen(
                [cf, "tunnel", "--no-autoupdate", "--url", f"http://{HOST}:{port}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as e:
            print(t("tunnel_cf_start_failed", err=e))
            self.proc = None
            return None

        self.url = None
        found = threading.Event()

        def reader():
            for line in self.proc.stdout:  # blijft draaien zodat de pipe niet vol loopt
                if not self.url:
                    m = TUNNEL_URL_RE.search(line)
                    if m:
                        self.url = m.group(0)
                        found.set()

        threading.Thread(target=reader, daemon=True).start()

        deadline = time.time() + TUNNEL_TIMEOUT
        while time.time() < deadline and not found.is_set():
            if self.proc.poll() is not None:
                break
            time.sleep(0.2)

        if not self.url:
            print(t("tunnel_timeout"))
            self.stop()
            return None

        db_log(f"Tunnel started: {self.url}")
        return self.url

    def stop(self):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            self.proc = None
            self.url = None


def copy_to_clipboard(text):
    if os.name != "nt":
        return False
    try:
        subprocess.run(["clip"], input=text.encode("utf-16le"), check=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except (OSError, subprocess.SubprocessError):
        return False


# ----------------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg=None):
    try:
        input(msg if msg is not None else t("back"))
    except EOFError:
        pass


def ask_port(default):
    raw = input(t("ask_port", default=default)).strip()
    if raw.isdigit() and 1024 <= int(raw) <= 65535:
        return int(raw)
    if raw:
        print(t("bad_port", raw=raw, default=default))
    return default


def start_server_with_fallback(server, wanted):
    port = find_free_port(wanted)
    if port is None:
        print(t("no_free_port"))
        return False
    if port != wanted:
        print(t("port_busy", wanted=wanted, port=port))
    try:
        server.start(port)
    except OSError as e:
        print(t("server_start_failed", err=e))
        return False
    db_log(f"Server started on port {port}")
    return True


def language_menu(cfg):
    avail = t.available()
    codes = list(avail)
    print("\n" + t("lang_header"))
    print(t("lang_current", name=avail.get(t.code, t.code)))
    for n, c in enumerate(codes, 1):
        print(t("lang_list_item", n=n, native=avail[c], code=c))
    print(t("lang_update"))
    choice = input(t("lang_prompt")).strip().lower()
    if choice == "u":
        if update_translations(cfg):
            t.set(t.code)  # direct herladen
    elif choice.isdigit() and 1 <= int(choice) <= len(codes):
        t.set(codes[int(choice) - 1])
        cfg["language"] = t.code
        save_config(cfg)
        print(t("lang_set", name=avail[t.code]))
    pause()


def main():
    # Emoji/UTF-8 in de Windows-console
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    setup_environment()
    cfg = load_config()
    t.set(pick_initial_language(cfg))
    if cfg.get("language") != t.code and "--lang" in sys.argv:
        cfg["language"] = t.code  # installer-keuze onthouden
        save_config(cfg)

    server = WebServer()
    tunnel = Tunnel()

    clear()
    line = "=" * 50
    print(line)
    print("   " + t("app_title", v=APP_VERSION))
    print(line)
    port = ask_port(cfg.get("port", DEFAULT_PORT))
    if not start_server_with_fallback(server, port):
        pause(t("exit_prompt"))
        return
    cfg["port"] = server.port
    save_config(cfg)

    try:
        while True:
            on = "🟢 " + t("online")
            off = "🔴 " + t("offline")
            server_status = on if server.is_running() else off
            db_status = on if check_db_status() else off
            tun_status = f"🟢 {tunnel.url}" if tunnel.is_running() and tunnel.url else "⚪ " + t("off")

            clear()
            print(line)
            print("      " + t("menu_title"))
            print(line)
            print(f" {t('s_http')}: {server_status} ({t('s_port')}: {server.port})")
            print(f" {t('s_db')}: {db_status}")
            print(f" {t('s_tunnel')}: {tun_status}")
            print(f" {t('s_folder')}: {WEB_ROOT}")
            print(f" {t('s_url')}: http://localhost:{server.port}")
            print("-" * 50)
            for k in ("m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"):
                print(" " + t(k))
            print(line)

            keuze = input(t("choose")).strip()

            if keuze == "1":
                webbrowser.open(f"http://localhost:{server.port}")
                pause()
            elif keuze == "2":
                print("\n" + t("files_header", dir=DIRECTORY))
                try:
                    for name in sorted(os.listdir(WEB_ROOT)):
                        print(f" - {name}")
                except OSError as e:
                    print(t("dir_failed", err=e))
                print("\n" + t("files_tip"))
                pause()
            elif keuze == "3":
                url = tunnel.start(server.port)
                if url:
                    print("\n" + t("tunnel_ready", url=url))
                    if copy_to_clipboard(url):
                        print(t("tunnel_copied"))
                    print(t("tunnel_keep_open"))
                pause()
            elif keuze == "4":
                print("\n" + t("logs_header"))
                try:
                    with db_connect() as conn:
                        for row in conn.execute(
                            "SELECT id, message, timestamp FROM logs ORDER BY id DESC LIMIT 10"
                        ):
                            print(f"[{row[0]}] {row[1]} ({row[2]})")
                except sqlite3.Error as e:
                    print(t("db_error", err=e))
                pause()
            elif keuze == "5":
                new_port = ask_port(server.port)
                tunnel.stop()  # tunnel wijst anders naar de oude poort
                if start_server_with_fallback(server, new_port):
                    cfg["port"] = server.port
                    save_config(cfg)
                pause()
            elif keuze == "6":
                tunnel.stop()
                print(t("tunnel_stopped"))
                pause()
            elif keuze == "7":
                language_menu(cfg)
            elif keuze == "8":
                break
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\n" + t("closing"))
        tunnel.stop()
        server.stop()
        db_log("SBserv closed.")


if __name__ == "__main__":
    main()
