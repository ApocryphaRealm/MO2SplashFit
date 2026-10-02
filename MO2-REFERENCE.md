# MO2 reference - the start-up splash (for MO2SplashFit.py), read 2026-10-02

Preflight rule: a plugin of ours that touches an MO2 feature records how MO2 itself implements that feature. Source:
`ModOrganizer2/modorganizer` at tag **v2.5.2**, `src/moapplication.cpp`.

**When the splash is made**
- `MOApplication::doOneRun()` constructs `MOSplash splash(*m_settings, m_instance->directory(), m_instance->gamePlugin())`
  right after the "splash" timing point, before the main window, and closes it with `splash.close()` just before
  `exec()`.
- So the file is read at the start of EVERY run, including the re-runs `doOneRun` makes after an instance change or
  restart. Plugins initialise later, so a plugin can only prepare `splash.png` for the next run.

**Which file**
- `MOSplash::getSplashPath()` returns nothing when `settings.useSplash()` is off.
- Otherwise it takes `<dataPath>/splash.png` if it exists and loads as a QImage.
- Failing that it falls back to the game plugin's `:/<shortName>/splash` resource, which it SAVES to
  `<dataPath>/splash.png` (so a missing splash.png is recreated from the game plugin's), and finally to
  `:/MO/gui/splash`.

**How it is shown**
- `QPixmap image(splashPath); ss_.reset(new QSplashScreen(image)); settings.geometry().centerOnMainWindowMonitor(ss_.get()); ss_->show();`
- No scaling by MO2. The pixmap has a device-pixel ratio of 1, so its pixel size is its LOGICAL size, and Qt scales it
  by the monitor's display scaling.
- So a splash fills the monitor only when its pixels equal the monitor's logical size. For example 3840x2160 at 175%
  is 2194x1234; the 2133x1200 splash covered about 97% of it.

**How MO2 Splash Fit follows it**
- It writes `<instance>/splash.png` at the logical size of the monitor MO2's main window is on (the monitor
  `centerOnMainWindowMonitor` uses).
- It writes only when the source art or the size changes.
- The original is kept once as `splash-original.png`.
- It never touches `useSplash`.
