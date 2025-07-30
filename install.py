import os
import platform
import subprocess
from pathlib import Path

LINUX = 0
WINDOWS = 0
GITREPO = "https://github.com/gioseaxmc/swami.git"

if platform.system().lower() == "linux":
    LINUX = 1
elif platform.system().lower() == "windows":
    import winreg
    WINDOWS = 1
else:
    print("Unsupported platform")

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
        winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, user_path+new_path+";")

def linux_add_to_path(executable_path: Path):
    subprocess.run(["ln", str(executable_path), "/usr/local/bin/swami"])

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
    install_dir = "/opt/swami" if LINUX else os.path.join(os.getenv("APPDATA"), ".swami")
    executable_path = os.path.join(install_dir, "swami" if LINUX else "swami.bat")

    if subprocess.run([
        "git",
        "clone",
        GITREPO,
        install_dir,
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
