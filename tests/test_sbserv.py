"""Rooktests voor SBserv. Draai:  python -m unittest discover -s tests -v
Draait zonder internet en zonder echte cloudflared (er wordt een nep-programma gebruikt)."""
import importlib
import json
import os
import socket
import stat
import sys
import tempfile
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def load_app(tmp):
    """Importeer sbserv met een lege, schrijfbare datamap (kopie van assets)."""
    import shutil
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(tmp, "assets"))
    shutil.copy(os.path.join(ROOT, "sbserv.py"), tmp)
    sys.path.insert(0, tmp)
    sys.modules.pop("sbserv", None)
    return importlib.import_module("sbserv")


class SBservTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.app = load_app(cls.tmp)
        cls.app.setup_environment()

    def test_environment_files(self):
        names = os.listdir(self.app.WEB_ROOT)
        for n in ("index.html", "logo.png", "favicon.ico"):
            self.assertIn(n, names)
        self.assertTrue(self.app.check_db_status())

    def test_user_index_not_overwritten(self):
        p = os.path.join(self.app.WEB_ROOT, "index.html")
        open(p, "w").write("mine")
        self.app.setup_environment()
        self.assertEqual(open(p).read(), "mine")

    def test_port_fallback_and_restart(self):
        blocker = socket.socket()
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        busy = blocker.getsockname()[1]
        s = self.app.WebServer()
        try:
            self.assertTrue(self.app.start_server_with_fallback(s, busy))
            self.assertNotEqual(s.port, busy)
            self.assertEqual(urllib.request.urlopen(f"http://127.0.0.1:{s.port}").status, 200)
            first = s.port
            self.assertTrue(self.app.start_server_with_fallback(s, first + 20))
            self.assertTrue(s.is_running())
            with self.assertRaises(Exception):
                urllib.request.urlopen(f"http://127.0.0.1:{first}", timeout=1)
        finally:
            s.stop()
            blocker.close()
        self.assertFalse(s.is_running())

    def test_languages(self):
        t = self.app.t
        self.assertEqual(set(t.available()) >= {"en", "nl"}, True)
        en = json.load(open(os.path.join(ROOT, "assets/lang/en.json"), encoding="utf-8"))
        nl = json.load(open(os.path.join(ROOT, "assets/lang/nl.json"), encoding="utf-8"))
        self.assertEqual(set(en), set(nl), "en en nl moeten dezelfde sleutels hebben")
        t.set("nl")
        self.assertIn("HOOFDMENU", t("menu_title"))
        t.set("xx")  # onbekend -> Engels
        self.assertIn("MAIN MENU", t("menu_title"))

    def test_broken_translation_falls_back(self):
        t = self.app
        json.dump({"_meta": {}, "port_busy": "{kapot"},
                  open(os.path.join(t.USER_LANG_DIR, "de.json"), "w"))
        t.t.set("de")
        self.assertIn("in use", t.t("port_busy", wanted=1, port=2))

    def test_tunnel_with_fake_cloudflared(self):
        if os.name == "nt":
            self.skipTest("nep-cloudflared is een shell-script")
        a = self.app
        fake = os.path.join(a.BIN_DIR, a.CF_NAME)
        with open(fake, "w") as f:
            f.write("#!/bin/sh\nif [ \"$1\" = --version ]; then echo 'cloudflared version 1'; exit 0; fi\n"
                    "echo 'INF https://abc-def-1.trycloudflare.com'\nsleep 20\n")
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        a.has_internet = lambda timeout=4: True
        tun = a.Tunnel()
        try:
            self.assertEqual(tun.start(8080), "https://abc-def-1.trycloudflare.com")
            self.assertTrue(tun.is_running())
        finally:
            tun.stop()
        self.assertFalse(tun.is_running())

    def test_tunnel_without_internet(self):
        a = self.app
        a.has_internet = lambda timeout=4: False
        a.find_cloudflared = lambda: "x"
        self.assertIsNone(a.Tunnel().start(8080))


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.app = a = load_app(cls.tmp)
        a.setup_environment()
        a.t.set("en")
        a.CTX.cfg = {}
        a.start_server_with_fallback(a.CTX.server, 18200)
        a.CTX.admin = a.AdminServer()
        assert a.CTX.admin.start(18300)
        cls.base = f"http://127.0.0.1:{a.CTX.admin.port}"
        cls.token = a.CTX.admin.token

    @classmethod
    def tearDownClass(cls):
        cls.app.CTX.tunnel.stop()
        cls.app.CTX.server.stop()
        cls.app.CTX.admin.stop()

    def req(self, path, method="GET", body=None, token=True, host=None):
        import urllib.error
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-SBserv-Token"] = self.token
        if host:
            headers["Host"] = host
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(r, timeout=5) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_page_and_token(self):
        code, body = self.req("/", token=False)
        self.assertEqual(code, 200)
        self.assertIn(self.token.encode(), body)
        self.assertNotIn(b"__TOKEN__", body)

    def test_api_requires_token_and_host(self):
        self.assertEqual(self.req("/api/status", token=False)[0], 403)
        self.assertEqual(self.req("/api/status", host="evil.example")[0], 403)
        self.assertEqual(self.req("/api/status")[0], 200)

    def test_status_shape(self):
        j = json.loads(self.req("/api/status")[1])
        self.assertTrue(j["web"]["online"])
        self.assertTrue(j["db"]["online"])
        self.assertEqual(j["tunnel"]["state"], "off")
        self.assertIn("nl", j["languages"])

    def test_db_read_only_and_injection(self):
        self.assertEqual(json.loads(self.req("/api/db")[1]), ["logs", "users"])
        code, body = self.req("/api/db/logs")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["columns"], ["id", "message", "timestamp"])
        self.assertEqual(self.req("/api/db/" + urllib.request.quote('logs";DROP TABLE logs;--'))[0], 404)
        self.assertEqual(json.loads(self.req("/api/db")[1]), ["logs", "users"])

    def test_settings_validation_and_language(self):
        self.assertEqual(self.req("/api/settings", "POST", {"port": 80})[0], 400)
        self.assertEqual(self.req("/api/settings", "POST", {"port": "abc"})[0], 400)
        self.assertEqual(self.req("/api/settings", "POST", {"language": "zz"})[0], 400)
        self.assertEqual(self.req("/api/settings", "POST", {"ui_size": "xl"})[0], 400)
        self.assertEqual(self.req("/api/settings", "POST", {"language": "nl", "ui_size": "l"})[0], 200)
        strings = json.loads(self.req("/api/strings")[1])
        self.assertEqual(strings["st_web"], "Webserver")
        self.assertEqual(self.req("/api/settings", "POST", {"language": "en"})[0], 200)

    def test_tunnel_errors_and_fake_tunnel(self):
        a = self.app
        a.has_internet = lambda timeout=4: False
        self.req("/api/tunnel/start", "POST", {})
        import time
        for _ in range(30):
            st = json.loads(self.req("/api/status")[1])["tunnel"]
            if st["state"] == "off" and st["error"]:
                break
            time.sleep(0.1)
        self.assertEqual(st["error"], "no_internet")
        if os.name == "nt":
            return
        fake = os.path.join(a.BIN_DIR, a.CF_NAME)
        with open(fake, "w") as f:
            f.write("#!/bin/sh\nif [ \"$1\" = --version ]; then echo 'cloudflared version 1'; exit 0; fi\n"
                    "echo 'INF https://dash-test-1.trycloudflare.com'\nsleep 20\n")
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        a.has_internet = lambda timeout=4: True
        self.req("/api/tunnel/start", "POST", {})
        for _ in range(50):
            st = json.loads(self.req("/api/status")[1])["tunnel"]
            if st["state"] == "live":
                break
            time.sleep(0.1)
        self.assertEqual(st["url"], "https://dash-test-1.trycloudflare.com")
        self.req("/api/tunnel/stop", "POST", {})
        for _ in range(30):
            st = json.loads(self.req("/api/status")[1])["tunnel"]
            if st["state"] == "off":
                break
            time.sleep(0.1)
        self.assertEqual(st["state"], "off")
        self.assertIsNone(st["error"])

    def test_admin_not_on_public_server(self):
        import urllib.error
        port = self.app.CTX.server.port
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status")
        self.assertNotIn(b"sbserv-token", urllib.request.urlopen(f"http://127.0.0.1:{port}/").read())


class AuthTests(unittest.TestCase):
    """Gebruikers, wachtwoord-hash en login-API."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.app = a = load_app(cls.tmp)
        a.setup_environment()
        a.t.set("en")
        a.CTX.cfg = {}
        a.start_server_with_fallback(a.CTX.server, 18400)
        a.CTX.admin = a.AdminServer()
        assert a.CTX.admin.start(18500)
        cls.pub = f"http://127.0.0.1:{a.CTX.server.port}"
        cls.adm = f"http://127.0.0.1:{a.CTX.admin.port}"

    @classmethod
    def tearDownClass(cls):
        cls.app.CTX.server.stop()
        cls.app.CTX.admin.stop()

    def setUp(self):
        self.app.THROTTLE.fails.clear()
        self.app.CTX.cfg["allow_register"] = False
        with self.app.db_connect() as c:
            c.execute("DELETE FROM sessions")
            c.execute("DELETE FROM users")

    def call(self, base, path, method="GET", body=None, headers=None, token=False):
        import urllib.error
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        if token:
            h["X-SBserv-Token"] = self.app.CTX.admin.token
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(r, timeout=5) as resp:
                return resp.status, self._j(resp.read()), resp.headers
        except urllib.error.HTTPError as e:
            return e.code, self._j(e.read()), e.headers

    @staticmethod
    def _j(raw):
        try:
            return json.loads(raw or b"{}")
        except ValueError:
            return {}

    def login(self, user="ouwe", pw="geheim1234"):
        return self.call(self.pub, "/api/auth/login", "POST", {"username": user, "password": pw})

    def test_hash_is_salted_and_verifies(self):
        a = self.app
        h1, h2 = a.hash_password("geheim1234"), a.hash_password("geheim1234")
        self.assertNotEqual(h1, h2)
        self.assertNotIn("geheim1234", h1)
        self.assertTrue(a.verify_password("geheim1234", h1))
        self.assertFalse(a.verify_password("geheim1235", h1))
        self.assertFalse(a.verify_password("x", "kapot$hash"))

    def test_create_validation(self):
        a = self.app
        self.assertEqual(a.create_user("ab", "geheim1234"), (False, "username"))
        self.assertEqual(a.create_user("bad name!", "geheim1234"), (False, "username"))
        self.assertEqual(a.create_user("ouwe", "kort"), (False, "password"))
        self.assertEqual(a.create_user("ouwe", "geheim1234"), (True, None))
        self.assertEqual(a.create_user("OUWE", "geheim1234"), (False, "exists"))  # niet hoofdlettergevoelig

    def test_login_me_logout(self):
        self.app.create_user("ouwe", "geheim1234")
        self.assertEqual(self.call(self.pub, "/api/auth/me")[0], 401)
        code, j, hd = self.login()
        self.assertEqual(code, 200)
        cookie = hd["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        sid = cookie.split(";")[0]
        code, j, _ = self.call(self.pub, "/api/auth/me", headers={"Cookie": sid})
        self.assertEqual((code, j["user"]), (200, "ouwe"))
        self.call(self.pub, "/api/auth/logout", "POST", {}, headers={"Cookie": sid})
        self.assertEqual(self.call(self.pub, "/api/auth/me", headers={"Cookie": sid})[0], 401)

    def test_wrong_password_unknown_user_same_error(self):
        self.app.create_user("ouwe", "geheim1234")
        c1, j1, _ = self.login(pw="fout-wachtwoord")
        c2, j2, _ = self.login(user="bestaatniet")
        self.assertEqual((c1, j1), (c2, j2))
        self.assertEqual(c1, 401)

    def test_lockout_after_five_failures(self):
        self.app.create_user("ouwe", "geheim1234")
        for _ in range(5):
            self.assertEqual(self.login(pw="fout-wachtwoord")[0], 401)
        self.assertEqual(self.login()[0], 429)  # ook het juiste wachtwoord is nu even geblokkeerd

    def test_disabled_user_and_password_change_end_sessions(self):
        a = self.app
        a.create_user("ouwe", "geheim1234")
        uid = a.list_users()[0]["id"]
        sid = self.login()[2]["Set-Cookie"].split(";")[0]
        a.set_user_password(uid, "nieuwwachtwoord")
        self.assertEqual(self.call(self.pub, "/api/auth/me", headers={"Cookie": sid})[0], 401)
        self.assertEqual(self.login()[0], 401)
        self.assertEqual(self.login(pw="nieuwwachtwoord")[0], 200)
        a.set_user_disabled(uid, True)
        self.assertEqual(self.login(pw="nieuwwachtwoord")[0], 401)

    def test_csrf_checks(self):
        self.app.create_user("ouwe", "geheim1234")
        code = self.call(self.pub, "/api/auth/login", "POST", {"username": "ouwe", "password": "geheim1234"},
                         headers={"Origin": "http://evil.example"})[0]
        self.assertEqual(code, 403)
        code = self.call(self.pub, "/api/auth/login", "POST", {"username": "ouwe", "password": "geheim1234"},
                         headers={"Content-Type": "text/plain"})[0]
        self.assertEqual(code, 403)

    def test_register_closed_by_default_then_open(self):
        body = {"username": "gast", "password": "geheim1234"}
        self.assertEqual(self.call(self.pub, "/api/auth/register", "POST", body)[0], 403)
        self.app.CTX.cfg["allow_register"] = True
        code, j, hd = self.call(self.pub, "/api/auth/register", "POST", body)
        self.assertEqual((code, j["user"]), (200, "gast"))
        self.assertIn(self.app.SESSION_COOKIE, hd["Set-Cookie"])

    def test_dashboard_user_management_and_no_hash_leak(self):
        c, j, _ = self.call(self.adm, "/api/users", "POST", {"username": "ouwe", "password": "geheim1234"}, token=True)
        self.assertEqual(c, 200)
        self.assertEqual(self.call(self.adm, "/api/users", "POST", {"username": "ouwe", "password": "geheim1234"}, token=True)[0], 400)
        self.assertEqual(self.call(self.adm, "/api/users", "POST", {"username": "x", "password": "geheim1234"})[0], 403)  # zonder token
        rows = self.call(self.adm, "/api/users", token=True)[1]
        self.assertEqual([r["username"] for r in rows], ["ouwe"])
        self.assertNotIn("pw_hash", rows[0])
        db = self.call(self.adm, "/api/db", token=True)[1]
        self.assertNotIn("sessions", db)
        users = self.call(self.adm, "/api/db/users", token=True)[1]
        self.assertTrue(all(r[users["columns"].index("pw_hash")] == "********" for r in users["rows"]))
        self.assertEqual(self.call(self.adm, "/api/db/sessions", token=True)[0], 404)
        uid = rows[0]["id"]
        self.assertEqual(self.call(self.adm, "/api/users/disable", "POST", {"id": uid, "disabled": True}, token=True)[0], 200)
        self.assertEqual(self.login()[0], 401)
        self.assertEqual(self.call(self.adm, "/api/users/delete", "POST", {"id": uid}, token=True)[0], 200)
        self.assertEqual(self.call(self.adm, "/api/users/delete", "POST", {"id": uid}, token=True)[0], 400)

    def test_auth_not_on_admin_and_not_shadowed_by_files(self):
        self.assertEqual(self.call(self.pub, "/api/auth/nothing")[0], 404)
        self.assertEqual(self.call(self.pub, "/api/users")[0], 404)  # beheer-API bestaat niet op de publieke site
        self.assertEqual(self.call(self.pub, "/api/auth/login", "POST", {"username": "a"})[0], 401)


class InstallerScriptTests(unittest.TestCase):
    """Het Inno-script moet kloppen met de app en naar bestaande bestanden verwijzen."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "sbserv_installer.iss"), encoding="utf-8") as f:
            cls.iss = f.read()

    def test_version_matches_app(self):
        m = __import__("re").search(r'#define MyAppVersion "([^"]+)"', self.iss)
        app = open(os.path.join(ROOT, "sbserv.py"), encoding="utf-8").read()
        self.assertEqual(m.group(1), __import__("re").search(r'APP_VERSION = "([^"]+)"', app).group(1))

    def test_referenced_files_exist(self):
        import re
        paths = re.findall(r'(?:SetupIconFile=|InfoBeforeFile: "|InfoAfterFile: ")([^";\r\n]+)', self.iss)
        paths += re.findall(r'WizardImageFile=([^\r\n]+)|WizardSmallImageFile=([^\r\n]+)', self.iss)
        flat = []
        for p in paths:
            flat += [x for x in (p if isinstance(p, tuple) else (p,)) for x in x.split(",") if x]
        self.assertGreaterEqual(len(flat), 9)
        for p in flat:
            self.assertTrue(os.path.exists(os.path.join(ROOT, p.strip().replace("\\", "/"))), p)

    def test_languages_and_info_pages(self):
        self.assertIn("Languages\\Dutch.isl", self.iss)
        self.assertFalse([l for l in self.iss.splitlines() if l.startswith("Name:") and "Dutchduc" in l])
        for code in ("en", "nl"):
            for kind in ("before", "after"):
                raw = open(os.path.join(ROOT, "installer", f"info_{kind}_{code}.txt"), "rb").read()
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))  # UTF-8 met BOM: ë/é blijven goed
                self.assertIn(b"\r\n", raw)

    def test_dark_wizard_guarded_for_old_inno(self):
        self.assertIn("WizardStyle=modern dark", self.iss)
        self.assertIn("#if Ver >= 0x06060000", self.iss)  # oudere Inno-versies kennen "dark" niet
        self.assertIn("WizardStyle=modern\n", self.iss.replace("\r\n", "\n"))

    def test_kit_script_and_uninstall_prompt(self):
        self.assertIn("KeepData", self.iss)
        self.assertIn("usPostUninstall", self.iss)
        kit = open(os.path.join(ROOT, "make_kit.bat"), "rb").read()
        self.assertIn(b"SBserv_kit", kit)
        self.assertIn(b"\r\n", kit)


if __name__ == "__main__":
    unittest.main()
