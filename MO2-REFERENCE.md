# MO2 reference - the start-up splash (for MO2SplashFit.py), read 2026-10-02

Preflight rule: a plugin of ours that touches an MO2 feature records how MO2 itself implements that feature.

**MO2 version:** 2.5.2 (tag `v2.5.2` of `ModOrganizer2/modorganizer`).

**Source read:**
- [src/moapplication.cpp](https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/moapplication.cpp):
  `MOApplication::doOneRun`, `MOSplash`, `MOSplash::getSplashPath`.
- [src/settings.cpp](https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/settings.cpp):
  `GeometrySettings::centerOnMainWindowMonitor`, `centerOnMonitor`, `saveMainWindowMonitor`.

## What MO2 does

| Step | MO2 2.5.2 | Where |
|---|---|---|
| Plugins load | `m_plugins = std::make_unique<PluginContainer>(...)`, then `m_plugins->loadPlugins()` | moapplication.cpp 268-272 |
| Splash made | `MOSplash splash(*m_settings, m_instance->directory(), m_instance->gamePlugin())`, after OrganizerCore setup and before the main window | moapplication.cpp 314-316 |
| Splash closed | `splash.close()` just before the main loop | moapplication.cpp 358 |
| Which file | Nothing if `settings.useSplash()` is off. Otherwise `<dataPath>/splash.png` if it loads as a QImage. Failing that, the game plugin's `:/<shortName>/splash`, which it SAVES as `<dataPath>/splash.png`. Finally `:/MO/gui/splash`. | moapplication.cpp 687-722 |
| How shown | `QPixmap image(splashPath); ss_.reset(new QSplashScreen(image)); centerOnMainWindowMonitor(...)`. No scaling by MO2: the pixmap's pixel size is its LOGICAL size, which Qt scales by the monitor's display scaling. | moapplication.cpp 657-676 |
| Which monitor | `[Geometry] MainWindow_monitor` from `ModOrganizer.ini`, an index into `QGuiApplication::screens()`. The primary screen when it is -1 or out of range. Written by `saveMainWindowMonitor` when the main window closes. | settings.cpp 926-968 |

So the splash is read on every run, including the re-runs `doOneRun` makes after an instance change. It fills the
monitor only when its pixels equal the monitor's logical size: for example 3840x2160 at 175% is 2194x1234, and a
2133x1200 splash covers about 97% of it.

## What MO2 Splash Fit does, and how it follows MO2

| Ours | Follows MO2 how |
|---|---|
| Fits `<instance>/splash.png` in `init()` | Plugins load before `MOSplash` is made, so the fitted file is the one shown on the same start. |
| Uses the monitor from `[Geometry] MainWindow_monitor`, else primary | Same key and same fallback as `centerOnMainWindowMonitor`. Read-only, through QSettings. |
| Fits to `QScreen.size()` (logical pixels) | `QSplashScreen` shows the pixmap at its pixel size as logical pixels. |
| Picks the closest-shaped `splash/splash-*.png`, scales to cover, centre-crops | Not an MO2 feature: MO2 has one file and never resizes it. |
| "Already fitted" also needs the file on disk to be that size | MO2 recreates a missing `splash.png` from the game plugin, at the wrong size; that is fitted again. |
| Checks the main window's monitor in `onUserInterfaceInitialized` | Backstop: if the window lands elsewhere, the next start's splash is fitted there. |
| Keeps the original once as `splash-original.png`; never touches `useSplash` | MO2's own setting stays the player's. |

## Departures to revisit

- **Corrected 2026-10-02.** The first build believed plugins initialise after the splash, so it fitted only for the
  next start. The owner, on the first start after a display change: "The image that appeared just now was a lot
  smaller than the screen." Re-read before relying on the order in a later MO2 release (2.6+): if `MOSplash` ever
  moves above `loadPlugins`, the backstop still fits for the next start, and the README's claim of "same start" has to
  change.
- A monitor index saved by MO2 on a since-unplugged screen falls back to primary in both MO2 and ours.
