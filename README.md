# gposingway-linux

## Status
This is _very_ experimental/alpha software. You're free to try to use it, but
the author provides no warranty about fitness of use, and it may well destroy
your FFXIV install.

## What does it do?
Fundamentally this is fairly simple:
1. This script tries to probe where your FFXIV and matching Wine/Proton
   prefixes live (either via XLCore config, Steam library info, or environment
   variables [FFXIV_PATH, WINE_PREFIX]).
2. Downloads the [reshade-linux](https://github.com/kevinlekiller/reshade-steam-proton)
   installer and runs this against your FFXIV directory.
3. Fixes `d3dcompiler_47.dll` in your Wine prefix.
4. Downloads the [GPosingway](https://github.com/gposingway/gposingway)
   shaders, presets, and configurations, and installs these to your FFXIV
   ReShade install.

This script uses `$XDG_DATA_HOME/gposingway_linux` as a working and storage
directory. The instances of ReShade and GPosingway used are targeted here, and
should not impact other installs of ReShade on your system.

## Supported use cases

For now, just installation. This should be safe to rerun for some classes of
updates, but _taps sign_ no warranties.

## Support

This tool is not associated with XLCore, GPosingway, ReShade, or kevinlekiller.
Don't bother them for support. If you find issues, you can create an issue up
above, but this was mostly created as a lark in an afternoon, so
run-of-the-mill support will likely be up to you as well.

## How To Run
You must have Poetry installed locally for this to execute - adding a
build/bootstrap script is on the to-do list.

```sh
poetry run python gposingway_linux
```

If `gposingway-linux` does not detect your FFXIV install, set the environment
variables menteioned above.
