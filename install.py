import os
import platform
import subprocess
from pathlib import Path

LINUX = 0
WINDOWS = 0

if platform.system().lower() == "linux":
    LINUX = 1
elif platform.system().lower() == "windows":
    import winreg
    WINDOWS = 1
else:
    print("Unsupported platform")

GITREPO = "https://github.com/gioseaxmc/swami.git"
INSTALLDIR = "/opt/swami" if LINUX else os.path.join(os.getenv("APPDATA"), ".swami")

print("Running installation script for", platform.system().lower())

if LINUX and os.geteuid() != 0:
    print("Please run as administrator")

def windows_add_to_path(executable_path: Path):
    new_path = str(executable_path.parent)
    with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Environment',
            0,
            winreg.KEY_READ | winreg.KEY_WRITE ) as key:
        user_path, _ = winreg.QueryValueEx(key, 'PATH')
        if new_path not in user_path:
            winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, user_path+new_path+";")
        else:
            print("swami already in path but not installed")

def linux_add_to_path(executable_path: Path):
    runner_script = f"""#!/bin/bash
python3.12 "{INSTALLDIR}/src/swami.py" $@
    """
    
    with open("/usr/local/bin/swami", "w") as fp:
        fp.write(runner_script)

    subprocess.run(["chmod", "+x", "/usr/local/bin/swami"])

def add_to_path(executable_path: str):
    a_exe_path = Path(executable_path).resolve()
    try:
        if LINUX:
            linux_add_to_path(a_exe_path)
        else:
            windows_add_to_path(a_exe_path)
        print("Added swami to path")
    except Exception as e:
        print("Couldnt add swami to path:", e)
        return 1
    return 0
        

def main():
    executable_path = os.path.join(INSTALLDIR, "swami" if LINUX else "swami.bat")

    if subprocess.run([
        "git",
        "clone",
        GITREPO,
        INSTALLDIR,
        "--depth",
        "1"
    ]).returncode:
        print("Couldnt clone into", GITREPO)
        return 1

    return add_to_path(executable_path)

if main():
    print("Failed to install")
else:
    print("Installation successful")
