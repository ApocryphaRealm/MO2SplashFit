r"""MO2 Splash Fit - Mod Organizer 2's start-up splash sized to the monitor it opens on.

For modlist authors (Wabbajack lists and any other MO2 instance that ships a splash.png): put your splash art at
several screen shapes in a "splash" folder beside splash.png - splash-16x9.png, splash-16x10.png, splash-21x9.png,
splash-4x3.png, and so on (any names starting "splash-" and ending ".png"; the shape is read from each image). Every
player then gets a splash that fills their screen, whatever its resolution, shape and Windows display scaling.

Why a plugin is needed (MO2 2.5.2, moapplication.cpp, MOSplash - see MO2-REFERENCE.md): at the start of every run,
BEFORE any plugin initialises, MO2 loads <instance>/splash.png into a QSplashScreen at the image's own pixel size - which
Qt then scales by the monitor's display scaling - centred on the main window's monitor. So a splash fills the screen only
when its pixel size equals that monitor's LOGICAL size (3840x2160 at 175% scaling is 2194x1234), and a plugin can only
prepare the file for the NEXT start.

What it does: once MO2's window exists, it reads that window's monitor (logical size), picks the art in splash/ whose
shape is closest, scales it to cover that size exactly (a sliver is trimmed when the shape is not identical) and writes
splash.png - only when that differs from what is already there. The first start after a display change still shows the
previous splash; every start after fits. The original splash.png is kept once as splash-original.png. What it chose is
logged to plugins/data/mo2-splash-fit.log.

Made for the Njordlinger modlist (2026-10-02) - the owner: the splash "doesnt fill the screen all the way on different
resolutions". Apocrypha Menu Framework 2.0.2+ (Skyrim) reads the same splash/ folder for its start-up curtain in game.
"""
import json
import math
import os
import shutil
import time
import traceback

try:
    from PyQt6.QtCore import Qt, QRect
    from PyQt6.QtGui import QImage, QGuiApplication
    from PyQt6.QtWidgets import QApplication
    KEEP_EXPANDING = Qt.AspectRatioMode.KeepAspectRatioByExpanding
    SMOOTH = Qt.TransformationMode.SmoothTransformation
except ImportError:
    from PyQt5.QtCore import Qt, QRect
    from PyQt5.QtGui import QImage, QGuiApplication
    from PyQt5.QtWidgets import QApplication
    KEEP_EXPANDING = Qt.KeepAspectRatioByExpanding
    SMOOTH = Qt.SmoothTransformation

import mobase

__version__ = "1.0.0"    # issued by version-gate.ps1; never typed by hand

VARIANT_DIR = "splash"
STATE_FILE = "splash-fit.json"   # in the variant folder: what splash.png was last made from
LOG_LINES = 200


class MO2SplashFit(mobase.IPlugin):
    def __init__(self):
        super().__init__()
        self._organizer = None

    def init(self, organizer):
        self._organizer = organizer
        try:
            organizer.onUserInterfaceInitialized(self._on_ui)
        except Exception:
            self._log("could not register for the main window:\n" + traceback.format_exc())
        return True

    # every slot is guarded: PyQt6 aborts MO2 (qFatal) when a Python slot raises
    def _on_ui(self, window):
        try:
            self._fit(window)
        except Exception:
            self._log("splash fit failed (MO2 keeps the current splash):\n" + traceback.format_exc())

    def _instance_dir(self):
        # splash.png lives where MO2's dataPath points - the instance folder (a portable instance: the MO2 folder)
        try:
            return os.path.normpath(self._organizer.basePath())
        except Exception:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _fit(self, window):
        if self._organizer.pluginSetting(self.name(), "enabled") is False:
            self._log("switched off in the plugin settings")
            return
        base = self._instance_dir()
        folder = os.path.join(base, VARIANT_DIR)
        if not os.path.isdir(folder):
            self._log(f"no {folder} folder - nothing to fit")
            return
        screen = window.screen() if window is not None and hasattr(window, "screen") else None
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        size = screen.size()                       # logical pixels - what QSplashScreen's pixmap is measured in
        tw, th = size.width(), size.height()
        if tw <= 0 or th <= 0:
            return
        target = tw / th
        variants = []
        for f in sorted(os.listdir(folder)):
            if f.lower().startswith("splash-") and f.lower().endswith(".png"):
                img = QImage(os.path.join(folder, f))
                if not img.isNull() and img.height() > 0:
                    variants.append((abs(math.log((img.width() / img.height()) / target)), f, img))
        if not variants:
            self._log(f"no splash-*.png in {folder}")
            return
        variants.sort(key=lambda v: v[0])
        _, name, img = variants[0]

        state_path = os.path.join(folder, STATE_FILE)
        want = {"source": name, "width": tw, "height": th,
                "source_mtime": int(os.path.getmtime(os.path.join(folder, name)))}
        splash = os.path.join(base, "splash.png")
        try:
            with open(state_path, encoding="utf-8") as fh:
                have = json.load(fh)
        except Exception:
            have = None
        if have == want and os.path.exists(splash):
            self._log(f"already fitted: {name} at {tw}x{th}")
            return

        original = os.path.join(base, "splash-original.png")
        if os.path.exists(splash) and not os.path.exists(original):
            shutil.copy2(splash, original)

        scaled = img.scaled(tw, th, KEEP_EXPANDING, SMOOTH)
        x = (scaled.width() - tw) // 2
        y = (scaled.height() - th) // 2
        out = scaled.copy(QRect(x, y, tw, th))
        tmp = splash + ".tmp"
        if not out.save(tmp, "PNG"):
            self._log(f"could not write {tmp}")
            return
        os.replace(tmp, splash)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(want, fh, indent=1)
        self._log(f"splash.png fitted from {name} to {tw}x{th} (monitor {screen.name()}, "
                  f"{screen.devicePixelRatio():.2f}x scaling) - shown from the next start")

    def _log(self, text):
        # a file of its own: MO2's own log does not reliably carry Python plugins' output. Kept short (the newest
        # LOG_LINES lines), since it gains a line every time MO2 starts.
        try:
            path = os.path.join(QApplication.applicationDirPath(), "plugins", "data", "mo2-splash-fit.log")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            lines = []
            if os.path.exists(path):
                with open(path, encoding="utf-8", errors="replace") as fh:
                    lines = fh.read().splitlines()
            lines.append(time.strftime("%Y-%m-%d %H:%M:%S ") + text)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines[-LOG_LINES:]) + "\n")
        except Exception:
            pass

    def name(self):
        return "MO2 Splash Fit"

    def localizedName(self):
        return self.name()

    def author(self):
        return "ApocryphaRealm"

    def description(self):
        return ("Fits Mod Organizer's start-up splash to the monitor it opens on: picks the closest-shaped art in the "
                "instance's splash folder and sizes splash.png to the screen, for the next start.")

    def version(self):
        major, minor, patch = (int(x) for x in __version__.split("."))
        return mobase.VersionInfo(major, minor, patch, mobase.ReleaseType.FINAL)

    def settings(self):
        return [mobase.PluginSetting("enabled", "Fit splash.png to the monitor", True)]


def createPlugin():
    return MO2SplashFit()
