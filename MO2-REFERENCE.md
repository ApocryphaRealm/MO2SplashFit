# MO2 reference - the start-up splash (for MO2SplashFit.py), read 2026-10-02

Preflight rule: a plugin of ours that touches an MO2 feature records how MO2 itself implements that feature. Source:
`ModOrganizer2/modorganizer` at tag **v2.5.2**, `src/moapplication.cpp`.

**When the splash is made**
- `MOApplication::doOneRun()` constructs `MOSplash splash(*m_settings, m_instance->directory(), m_instance->gamePlugin())`
  right after the "splash" timing point, before the main window, and closes it with `splash.close()` just before
  `exec()`.
- So the file is read at the start of EVERY run, including the re-runs `doOneRun` makes after an instance change or
  restart.
- Plugins load EARLIER in the same function: `m_plugins = std::make_unique<PluginContainer>(...)` and
  `m_plugins->loadPlugins()` at the "plugins" timing point (lines 268-272), then OrganizerCore setup, then the splash
  (line 316). So a plugin's `init()` can write `splash.png` and MO2 shows the result on that same start.
- Corrected 2026-10-02. The first build believed plugins initialise after the splash, so it fitted only for the next
  start. The owner, on the first start after a display change: "The image that appeared just now was a lot smaller
  than the screen."

**Which monitor** (`src/settings.cpp`)
- `GeometrySettings::centerOnMainWindowMonitor` reads `[Geometry] MainWindow_monitor` from `ModOrganizer.ini`, an
  index into `QGuiApplication::screens()`, and `centerOnMonitor` falls back to the primary screen when it is -1 or out
  of range. `saveMainWindowMonitor` writes it when the main window closes.

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
- In `init()`, before MO2 reads the file, it writes `<instance>/splash.png` at the logical size of the monitor
  `centerOnMainWindowMonitor` will use. It reads the same INI key, with the same primary-screen fallback.
- When the main window opens (`onUserInterfaceInitialized`), it checks that window's monitor again and refits for the
  next start if the window landed elsewhere.
- "Already fitted" also requires the `splash.png` on disk to be at that size, so a file replaced by an author, or
  recreated by MO2 from the game plugin, is fitted again.
- It writes only when the source art or the size changes.
- The original is kept once as `splash-original.png`.
- It never touches `useSplash`.
