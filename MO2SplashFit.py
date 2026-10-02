r"""MO2 Splash Fit - Mod Organizer 2's start-up splash sized to the monitor it opens on.

For modlist authors (Wabbajack lists and any other MO2 instance that ships a splash.png): put your splash art at
several screen shapes in a "splash" folder beside splash.png - splash-16x9.png, splash-16x10.png, splash-21x9.png,
splash-4x3.png, and so on (any names starting "splash-" and ending ".png"; the shape is read from each image). Every
player then gets a splash that fills their screen, whatever its resolution, shape and Windows display scaling.

Why a plugin is needed (MO2 2.5.2, moapplication.cpp, MOSplash - see MO2-REFERENCE.md): on every start MO2 loads
<instance>/splash.png into a QSplashScreen at the image's own pixel size - which Qt then scales by the monitor's display
scaling - centred on the main window's monitor. So a splash fills the screen only when its pixel size equals that
monitor's LOGICAL size (3840x2160 at 175% scaling is 2194x1234).

What it does: MO2 loads its plugins just BEFORE it reads splash.png, so when this plugin initialises it reads the monitor
the splash is about to appear on (ModOrganizer.ini [Geometry] MainWindow_monitor, as MO2 does), picks the art in splash/
whose shape is closest, scales it to cover that monitor's logical size exactly (a sliver is trimmed when the shape is
not identical) and writes splash.png - only when that differs from what is already there. The splash shown moments
later is the fitted one, on the very first start and after every display change (the owner, 2026-10-02, of an earlier
build that fitted for the next start only: "The image that appeared just now was a lot smaller than the screen"). When
the main window opens it checks again, in case the window landed on another monitor. The original splash.png is kept
once as splash-original.png. What it chose is logged to plugins/data/mo2-splash-fit.log.

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
    from PyQt6.QtCore import Qt, QRect, QSettings
    from PyQt6.QtGui import QImage, QImageReader, QGuiApplication
    from PyQt6.QtWidgets import QApplication
    KEEP_EXPANDING = Qt.AspectRatioMode.KeepAspectRatioByExpanding
    SMOOTH = Qt.TransformationMode.SmoothTransformation
except ImportError:
    from PyQt5.QtCore import Qt, QRect, QSettings
    from PyQt5.QtGui import QImage, QImageReader, QGuiApplication
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
            # MO2 loads plugins BEFORE it reads splash.png (doOneRun: loadPlugins, then MOSplash), so a fit made now
            # is the splash shown on this very start
            self._fit(self._splash_monitor())
        except Exception:
            self._log("splash fit failed (MO2 shows the current splash):\n" + traceback.format_exc())
        try:
            organizer.onUserInterfaceInitialized(self._on_ui)
        except Exception:
            self._log("could not register for the main window:\n" + traceback.format_exc())
        return True

    # every slot is guarded: PyQt6 aborts MO2 (qFatal) when a Python slot raises. A backstop: when the main window
    # opens on a monitor other than the one the splash was fitted to, splash.png is refitted for the next start.
    def _on_ui(self, window):
        try:
            screen = window.screen() if window is not None and hasattr(window, "screen") else None
            self._fit(screen)
        except Exception:
            self._log("splash fit failed (MO2 keeps the current splash):\n" + traceback.format_exc())

    def _instance_dir(self):
        # splash.png lives where MO2's dataPath points - the instance folder (a portable instance: the MO2 folder)
        try:
            return os.path.normpath(self._organizer.basePath())
        except Exception:
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _splash_monitor(self):
        # the monitor MO2 is about to show its splash on: GeometrySettings::centerOnMainWindowMonitor reads
        # [Geometry] MainWindow_monitor from ModOrganizer.ini (an index into QGuiApplication::screens()), else primary
        screens = QGuiApplication.screens()
        try:
            ini = QSettings(os.path.join(self._instance_dir(), "ModOrganizer.ini"), QSettings.Format.IniFormat)
            index = int(ini.value("Geometry/MainWindow_monitor", -1))
        except Exception:
            index = -1
        if 0 <= index < len(screens):
            return screens[index]
        return QGuiApplication.primaryScreen()

    def _fit(self, screen):
        # returns the path of a splash.png fitted to the screen, or None
        if self._organizer.pluginSetting(self.name(), "enabled") is False:
            self._log("switched off in the plugin settings")
            return None
        base = self._instance_dir()
        folder = os.path.join(base, VARIANT_DIR)
        if not os.path.isdir(folder):
            self._log(f"no {folder} folder - nothing to fit")
            return None
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        size = screen.size()                       # logical pixels - what QSplashScreen's pixmap is measured in
        tw, th = size.width(), size.height()
        if tw <= 0 or th <= 0:
            return None
        target = tw / th
        variants = []
        for f in sorted(os.listdir(folder)):
            if f.lower().startswith("splash-") and f.lower().endswith(".png"):
                img = QImage(os.path.join(folder, f))
                if not img.isNull() and img.height() > 0:
                    variants.append((abs(math.log((img.width() / img.height()) / target)), f, img))
        if not variants:
            self._log(f"no splash-*.png in {folder}")
            return None
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
        on_disk = QImageReader(splash).size() if os.path.exists(splash) else None   # replaced since? (an author, MO2)
        if have == want and on_disk is not None and (on_disk.width(), on_disk.height()) == (tw, th):
            self._log(f"already fitted: {name} at {tw}x{th}")
            return splash

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
            return None
        os.replace(tmp, splash)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(want, fh, indent=1)
        self._log(f"splash.png fitted from {name} to {tw}x{th} (monitor {screen.name()}, "
                  f"{screen.devicePixelRatio():.2f}x scaling)")
        return splash

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


# --- fault handling (standing rule, 2026-09-23: every MO2 plugin of ours logs and arms faulthandler) ---------------
def _arm_faulthandler():
    """Arm Python's faulthandler once per process, into plugins\\data\\faults.log. When MO2 dies inside C++ with a
    Python slot on the stack, the minidump names only modules; faulthandler writes the Python frames of every
    thread first, so the log names the plugin and the line. Whichever of our plugins loads first arms it."""
    try:
        import faulthandler
        if faulthandler.is_enabled():
            return
        here = os.path.abspath(__file__)
        while os.path.basename(here).lower() != "plugins":
            parent = os.path.dirname(here)
            if parent == here:
                return
            here = parent
        path = os.path.join(here, "data", "faults.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = open(path, "a", encoding="utf-8")
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + " faulthandler armed by " + os.path.basename(__file__) + chr(10))
        fh.flush()
        globals()["_FAULT_LOG_HANDLE"] = fh          # kept open for the life of the process
        faulthandler.enable(file=fh, all_threads=True)
    except Exception:  # noqa: BLE001
        pass


_arm_faulthandler()


def createPlugin():
    return MO2SplashFit()
