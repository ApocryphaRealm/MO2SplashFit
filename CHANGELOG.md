# Changelog - MO2 Splash Fit

Versions are issued by the project's version gate. Written as the change happens (rule 61).

## 1.0.0 - 2026-10-02 - first release

### The plugin

* Fits MO2's start-up splash to the player's monitor.
  * Once MO2's window is up, it reads that window's monitor at its logical size, which is what MO2's `QSplashScreen` is
    measured in.
  * It picks the `splash/splash-*.png` whose shape is closest, scales it to cover that size and crops the centre.
  * It writes the result as `splash.png`, for the next start.
* Writes only when the chosen picture or the screen size changes. A `splash-fit.json` in the `splash` folder records
  what was last written.
* Keeps the list's original `splash.png` once, as `splash-original.png`.
* One setting, "Fit splash.png to the monitor" (on).
* Logs to `plugins/data/mo2-splash-fit.log`, one line per start, trimmed to the newest 200 lines.
* Every slot is guarded, so an error is logged and the current splash stays. PyQt6 aborts MO2 when a Python slot raises.

### The author tool

* `tools/make_splash_variants.py` makes the seven shapes (16x9, 16x10, 21x9, 32x9, 4x3, 5x4, 3x2) from one master
  picture in frame, cover or pad mode.
* Frame mode reproduces the Njordlinger set pixel for pixel from its master.

### Development history before 1.0.0 (2026-10-02)

* Built as "Splash Fit" for the Njordlinger modlist. The owner: the splash "doesnt fill the screen all the way on
  different resolutions".
* The first build never ran its fit. The `isActive()` override reading a plugin setting was removed, and a log file of
  its own was added.
* Tested in MO2 2.5.2 on the owner's monitor:
  * 3200x1800 at 150% wrote 2133x1200 from splash-16x9.png.
  * After the owner switched to 1920x1080 at 125%, it wrote 1536x864. The next start logged "already fitted".
* The owner: the art should be "a selection of images that are fit for a range of resolutions so that it auto-selects
  the right one", not regenerated per PC. Then made a general modding tool, with the Njordlinger set as a demo for
  other Wabbajack list authors.
