MO2 Splash Fit
==============
Version 1.0.0

A Mod Organizer 2 plugin for MODLIST AUTHORS. It makes your list's start-up splash fill the player's screen, whatever
its resolution, shape (16:9, 16:10, 21:9, 4:3...) or Windows display scaling.

MO2 shows splash.png at the picture's own pixel size, so a single picture is too small, cut off, or barred on most
screens. With this plugin you ship the splash at several shapes. On every player's PC, the plugin sizes the closest one
to their monitor and writes it as splash.png. MO2 shows it from the next start.

THIS IS NOT A MOD. Do not install it with the mod manager.

REQUIREMENTS
------------
Mod Organizer 2 2.5.x (tested on 2.5.2).

INSTALLATION (in your modlist's MO2 folder)
-------------------------------------------
1. Copy plugins\MO2SplashFit.py into the MO2 folder's "plugins" folder.
2. Make a folder named "splash" next to splash.png. Put your splash in it at several shapes, named splash-<anything>.png
   (for example splash-16x9.png, splash-21x9.png, splash-4x3.png). The shape is read from each picture.
3. Start MO2. From the second start on, the splash fills the screen.

For a Wabbajack list, ship the plugin and the splash folder among the files your list installs into the MO2 folder.

MAKING THE SHAPES
-----------------
tools\make_splash_variants.py makes all seven shapes from one master picture. It needs Python 3 and Pillow
(pip install pillow). Run it with --help for the options:
  --mode frame   keeps a border's corners, stretches its edges and re-centres your lettering
  --mode cover   scales and crops a full-bleed picture
  --mode pad     fits the picture inside each shape on a plain background

DEMO
----
"Demo - Njordlinger splash" holds the seven shapes made for the Njordlinger modlist (frame mode). It shows what a
finished set looks like. It is an example, not something to install.

SETTINGS
--------
Settings -> Plugins -> MO2 Splash Fit -> "Fit splash.png to the monitor" (on). Turns it off without removing it.
Your original splash.png is kept once, as splash-original.png.

DEBUGGING
---------
<MO2 folder>\plugins\data\mo2-splash-fit.log has one line per start: which picture it chose, at what size. Send it with
any bug report.

LICENCE
-------
GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See LICENSE and NOTICE.md.
Source: https://github.com/ApocryphaRealm/MO2SplashFit
