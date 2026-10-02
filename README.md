# MO2 Splash Fit

A Mod Organizer 2 plugin for **modlist authors**. It makes your list's start-up splash fill the player's screen, whatever
its resolution, shape or Windows display scaling.

## The problem it solves

MO2 shows `splash.png` at the picture's own pixel size, scaled by Windows display scaling, in the middle of the monitor.
It never resizes the picture to the screen. A splash made at 1920x1080 is therefore:

* a box with a margin round it on a 4K screen at 100% scaling;
* cut off on a 1080p laptop at 125% scaling;
* bars on two sides on a 21:9 ultrawide or a 16:10 laptop.

No single picture fits every player.

## How it works

1. **You** ship the splash at several screen shapes in a `splash` folder beside `splash.png`:
   * `splash-16x9.png`, `splash-16x10.png`, `splash-21x9.png`, `splash-4x3.png` and so on;
   * any file named `splash-*.png` counts;
   * the shape is read from each picture, so the names are only for you.
2. When MO2's window opens, **the plugin** does four things:
   * reads the monitor the window is on;
   * picks the picture whose shape is closest;
   * scales it to that monitor's exact size, trimming a sliver if the shape is not identical;
   * writes it over `splash.png`.
3. **MO2** shows that file on every start after.

MO2 reads `splash.png` before any plugin loads, so a plugin can only prepare the file for the next start. The first start
on a new screen still shows the old splash; every start after fits. `MO2-REFERENCE.md` traces this through MO2's source
(`moapplication.cpp`, `MOSplash`, v2.5.2).

The plugin writes nothing unless the chosen picture or the screen size has changed. It keeps your original `splash.png`
once, as `splash-original.png`.

## For modlist authors

1. Make your variants. `tools/make_splash_variants.py` does it from one master picture (needs Python 3 and Pillow):
   * `--mode frame` keeps a border's corners as they are, stretches its straight edges and re-centres your lettering.
     The Njordlinger demo was made this way:
     `python make_splash_variants.py splash.png --corner 170 --text-box 238 501 1900 697`
   * `--mode cover` scales a full-bleed picture, such as a landscape or a screenshot, and crops it.
   * `--mode pad` fits the picture inside each shape on a plain background.

   Or make them by hand in any editor. Seven shapes at 2160 px tall cover almost every screen and are sharp at 4K.
2. Put the `splash` folder in your instance folder, next to `splash.png`.
3. Put `MO2SplashFit.py` in the instance's `plugins` folder.
4. Ship both with the list. For Wabbajack, include them in the files the list installs into the MO2 folder.

The Nexus download includes the Njordlinger set as a worked example: a bordered splash with centred lettering, at all
seven shapes. That set is a demonstration of the layout, not something to install as it is.

## Settings

| Setting | Default | What it does |
|---|---|---|
| Fit splash.png to the monitor | on | Turns the plugin off without removing it. |

Find it under Settings -> Plugins -> MO2 Splash Fit.

## Debugging

The plugin logs to `<MO2 folder>\plugins\data\mo2-splash-fit.log`. It writes one line per start, saying which picture it
chose and at what size, or that nothing needed doing. The log keeps the newest 200 lines.

## Also reads the same folder

From version 2.0.2, Apocrypha Menu Framework (Skyrim SE) takes the closest picture in the same `splash` folder for its
in-game start-up curtain.

## Requirements

Mod Organizer 2 2.5.x (tested on 2.5.2). There is a PyQt5 fallback for 2.4, but it is untested.

## Licence

GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See `LICENSE` and `NOTICE.md`.
