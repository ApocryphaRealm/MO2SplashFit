# MO2 Splash Fit - copyright and licence

Copyright (C) 2026 ApocryphaRealm

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program (`LICENSE`). If not, see
<https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later

## Why GPL-3.0-or-later

Every mod of this project is GPL-3.0-or-later by default (the owner, 2026-09-13). The plugin is one Python file of our
own. It runs inside Mod Organizer 2's Python plugin host (`mobase`, PyQt6) and links nothing else. The author tool,
`tools/make_splash_variants.py`, uses Pillow (MIT-CMU licence), which is installed separately.

## What it builds on

Mod Organizer 2 (https://github.com/ModOrganizer2/modorganizer, GPL-3.0) provides the plugin API
(`onUserInterfaceInitialized`, `basePath`, plugin settings) and reads the `splash.png` this plugin writes.

## The demo pictures

The Njordlinger splash set, which ships in the Nexus download only, is not part of this repository. The pictures are an
example of a finished set. They are not covered by this licence and are not for reuse in other lists.

Source code: https://github.com/ApocryphaRealm/MO2SplashFit
