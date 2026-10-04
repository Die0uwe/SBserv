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


if __name__ == "__main__":
    unittest.main()
