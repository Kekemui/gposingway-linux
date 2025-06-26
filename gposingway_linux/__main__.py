from configparser import ConfigParser, UNNAMED_SECTION
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

import vdf
from xdg_base_dirs import xdg_data_home

FFXIV_STEAM_APP_ID = 39210
WORKDIR:Path = xdg_data_home() / 'gposingway_linux'

FFXIV_PATH_ENV = 'FFXIV_PATH'
WINE_PREFIX_ENV = 'WINE_PREFIX'

class EnvInfo:
    def __init__(self):
        self.method = 'Environment'
        self.ffxiv_path = Path(os.getenv(FFXIV_PATH_ENV))
        self.wine_prefix = Path(os.getenv(WINE_PREFIX_ENV))
        self.valid = self.ffxiv_path != Path() and self.wine_prefix != Path()


class XLCoreInfo:
    def __init__(self):
        self.method = 'XLCore'
        self.ffxiv_path = None
        self.wine_prefix = None
        self.valid = False
        try:
            xlcore_path = Path.home() / '.xlcore'
            launcher_ini_path = xlcore_path / 'launcher.ini'
            launcher_config = ConfigParser(allow_unnamed_section=True, strict=False)
            launcher_config.read(launcher_ini_path)
            self.ffxiv_path = Path(launcher_config[UNNAMED_SECTION]['GamePath'])
            self.wine_prefix = xlcore_path / 'wineprefix'
            self.valid = True
        except KeyError:
            pass


class SteamInfo:
    def __find_ffxiv() -> list[Path]:
        with open(Path.home() / '.steam' / 'steam' / 'config'/ 'libraryfolders.vdf') as libvdf:
            libraries = vdf.load(libvdf)
        libs = []
        for lib in libraries['libraryfolders'].values():
            path = Path(lib['path'])
            if path.is_dir():
                libs.append(path)

        return next((x for x in libs if (x/'steamapps'/'appmanifest_39210.acf').exists()), None)


    def __init__(self):
        self.method = 'Steam'
        ffxiv_lib = SteamInfo.__find_ffxiv()
        if ffxiv_lib:
            steamapp_path = ffxiv_lib / 'steamapps'
            self.ffxiv_path = steamapp_path / 'common' / 'FINAL FANTASY XIV Online'
            self.wine_prefix = steamapp_path / 'compatdata' / str(FFXIV_STEAM_APP_ID) / 'pfx'
            self.valid = True
        else:
            self.ffxiv_path = self.wine_prefix = None
            self.valid = False


class LutrisInfo:
    pass

@dataclass
class ManualInfo:
    def __init__(self):
        pass

    @property
    def ffxiv_path(self) -> Path:
        # TODO Input and validation loop
        pass

    @property
    def wine_prefix(self) -> Path:
        # TODO Input and validation loop
        pass


def main():
    # Check pre-reqs
    if not shutil.which('git'):
        print("`git` not found on your path. Please install it and ensure it is accessible. Exiting.")
        exit(-1)

    # Initialize our workspace
    WORKDIR.mkdir(exist_ok=True)
    print(f"Using {str(WORKDIR)} as our working directory.")

    # Gather information
    infoset = [EnvInfo(), XLCoreInfo(), SteamInfo()]
    info = next(x for x in infoset if x.valid)

    print(f"Found the following FFXIV install information via {info.method}")
    print(f"\tGame location:\t{info.ffxiv_path}")
    print(f"\tWine prefix:\t{info.wine_prefix}")

    # Install ReShade using https://github.com/kevinlekiller/reshade-steam-proton

    RESHADE_INSTALLER_DIR = WORKDIR / 'reshade-installer'
    RESHADE_INSTALLER_DIR.mkdir(exist_ok=True)
    RESHADE_DATA_DIR = WORKDIR / 'reshade'

    reshade_install_env = {
        'MAIN_PATH': str(RESHADE_DATA_DIR),
        'SHADER_REPOS': '',
        'RESHADE_ADDON_SUPPORT': '1'
    }

    for k in os.environ:
        reshade_install_env[k] = os.environ[k]

    if not (RESHADE_INSTALLER_DIR / '.git').exists():
        print("Downloading ReShade installer...")
        subprocess.run(['git', 'clone', 'https://github.com/kevinlekiller/reshade-steam-proton.git', RESHADE_INSTALLER_DIR],
            capture_output=True,
            check=True)
        print("ReShade installer downloaded.")
    else:
        print("Getting updates for the ReShade installer...")
        subprocess.run(
            ['git', 'pull', '--rebase'],
            capture_output=True,
            check=True,
            cwd=RESHADE_INSTALLER_DIR
        )
        print("ReShade installer updated.")

    reshade_install_stdin = "\n".join(['i', str(info.ffxiv_path), 'y', 'n', '64', 'dxgi', 'y', ''])

    print(f"Installing ReShade for FFXIV at {info.ffxiv_path}...")
    subprocess.run(
        ['./reshade-linux.sh'],
        input=reshade_install_stdin,
        text=True,
        env=reshade_install_env,
        cwd=RESHADE_INSTALLER_DIR,
        capture_output=True
    )

    # reshade-linux.sh will tell the user to set WINEDLLOVERRIDES="d3dcompiler_47=n;dxgi=n,b"

    # Fix d3dcompiler_47.dll in Wine/Proton path

    sys32 = info.wine_prefix / 'drive_c' / 'windows' / 'system32'

    target_d3d:Path = sys32/'d3dcompiler_47.dll'
    if target_d3d.exists():
        print("Backing up current d3dcompiler_47.dll to d3dcompiler_47._dll. If a backup already exists here, it will be destroyed.")
        target_d3d.rename(sys32 / 'd3dcompiler_47._dll')

    print("Copying d3dcompiler_47.dll into your Wine/Proton environment")
    shutil.copy(info.ffxiv_path / 'd3dcompiler_47.dll', target_d3d)

    # Remove baseline shaders / ReShade config

    print("Cleaning out baseline shaders and configuration (you didn't want these).")
    (info.ffxiv_path / 'ReShade.ini').unlink()
    (info.ffxiv_path / 'ReShade_shaders').unlink()

    # Pull

    GPOSINGWAY_DIR = WORKDIR / 'gposingway'
    if not (GPOSINGWAY_DIR / '.git').exists():
        print("Downloading GPosingway...")
        subprocess.run(['git', 'clone', 'https://github.com/gposingway/gposingway.git', GPOSINGWAY_DIR],
            capture_output=True,
            check=True)
        print("GPosingway downloaded.")
    else:
        print("Getting updates for the ReShade installer...")
        subprocess.run(
            ['git', 'pull', '--rebase'],
            capture_output=True,
            check=True,
            cwd=GPOSINGWAY_DIR
        )
        print("GPosingway updated.")

    for f in ['reshade-presets', 'reshade-shaders']:
        (info.ffxiv_path / f).symlink_to(GPOSINGWAY_DIR / f)
    for f in ['ReShade.ini', 'ReShadePreset.ini']:
        shutil.copy(GPOSINGWAY_DIR / f, info.ffxiv_path / f)

    print("All done!")

    if info.method == 'Steam':
        print("You may need to set the following launch arguments for FFXIV in Steam: `WINEDLLOVERRIDES=\"d3dcompiler_47=n;dxgi=n,b\" %command%`")

if __name__ == '__main__':
    main()
