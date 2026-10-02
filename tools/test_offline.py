"""Offline test of MO2SplashFit.py: a stub mobase, PyQt6 offscreen, a scratch instance with a splash folder.

Checks: init() fits splash.png to MO2's saved splash monitor (before MO2 reads it); the closest shape is chosen and written at the screen's logical size; a second run writes nothing; the
original is kept once; the setting turns it off; a missing folder is logged, not raised.
Run: python tools/test_offline.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtGui import QImage, QColor          # noqa: E402
from PyQt6.QtWidgets import QApplication, QWidget  # noqa: E402

mobase = types.ModuleType("mobase")
mobase.IPlugin = type("IPlugin", (), {"__init__": lambda self: None})
mobase.VersionInfo = lambda *a: a
mobase.ReleaseType = types.SimpleNamespace(FINAL="final")
mobase.PluginSetting = lambda *a: a
sys.modules["mobase"] = mobase

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("MO2SplashFit", os.path.join(HERE, "..", "MO2SplashFit.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

app = QApplication(sys.argv)
logs = []
mod.MO2SplashFit._log = lambda self, t: logs.append(t)


class Organizer:
    def __init__(self, base):
        self.base, self.enabled, self.cb = base, True, None

    def basePath(self):
        return self.base

    def pluginSetting(self, plugin, key):
        return self.enabled

    def onUserInterfaceInitialized(self, cb):
        self.cb = cb


fails = 0


def check(cond, what):
    global fails
    print(("ok   " if cond else "FAIL ") + what)
    fails += 0 if cond else 1


base = tempfile.mkdtemp(prefix="sfit-")
try:
    os.makedirs(os.path.join(base, "splash"))
    for name, (w, h, col) in {"splash-16x9.png": (1600, 900, "red"), "splash-4x3.png": (1200, 900, "blue"),
                              "splash-21x9.png": (2100, 900, "green")}.items():
        img = QImage(w, h, QImage.Format.Format_RGB32)
        img.fill(QColor(col))
        img.save(os.path.join(base, "splash", name))
    orig = QImage(640, 360, QImage.Format.Format_RGB32)
    orig.fill(QColor("white"))
    orig.save(os.path.join(base, "splash.png"))

    org = Organizer(base)
    p = mod.MO2SplashFit()
    check(p.init(org) is True and org.cb is not None, "init registers for the main window")
    check(p.name() == "MO2 Splash Fit" and p.version()[:3] == (1, 0, 0), f"name and version {mod.__version__}")
    win = QWidget()
    scr = win.screen().size()
    org.cb(win)
    out = QImage(os.path.join(base, "splash.png"))
    check((out.width(), out.height()) == (scr.width(), scr.height()), f"splash.png is the screen's {scr.width()}x{scr.height()}")
    aspect = scr.width() / scr.height()
    expect = min({"red": 16 / 9, "blue": 4 / 3, "green": 21 / 9}.items(), key=lambda kv: abs(kv[1] / aspect - 1))[0]
    check(out.pixelColor(out.width() // 2, out.height() // 2) == QColor(expect), f"closest shape chosen ({expect})")
    check(QImage(os.path.join(base, "splash-original.png")).width() == 640, "original kept as splash-original.png")
    state = json.load(open(os.path.join(base, "splash", "splash-fit.json"), encoding="utf-8"))
    check(state["width"] == scr.width(), "state file written")

    mtime = os.path.getmtime(os.path.join(base, "splash.png"))
    logs.clear()
    org.cb(win)
    check(os.path.getmtime(os.path.join(base, "splash.png")) == mtime and "already fitted" in logs[-1], "second run writes nothing")
    check(QImage(os.path.join(base, "splash-original.png")).width() == 640, "original not overwritten by the fitted one")

    # first start on a new display: init() runs before MO2 reads splash.png, with no window yet
    for monitor in ("0", "7"):            # MO2's saved splash monitor; 7 does not exist -> primary, as MO2 does
        small = QImage(320, 180, QImage.Format.Format_RGB32)
        small.fill(QColor("white"))
        small.save(os.path.join(base, "splash.png"))
        with open(os.path.join(base, "ModOrganizer.ini"), "w", encoding="utf-8") as fh:
            fh.write(f"[Geometry]\nMainWindow_monitor={monitor}\n")
        logs.clear()
        p2 = mod.MO2SplashFit()
        p2.init(org)
        out = QImage(os.path.join(base, "splash.png"))
        check((out.width(), out.height()) == (scr.width(), scr.height()) and "fitted" in logs[-1],
              f"init fits splash.png before MO2 reads it (MainWindow_monitor={monitor})")

    org.enabled = False
    logs.clear()
    org.cb(win)
    check("switched off" in logs[-1], "setting off: nothing done")

    org.enabled = True
    shutil.rmtree(os.path.join(base, "splash"))
    logs.clear()
    org.cb(win)
    check("nothing to fit" in logs[-1], "no splash folder: logged, not raised")
finally:
    shutil.rmtree(base, ignore_errors=True)

print(f"{'all passed' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
