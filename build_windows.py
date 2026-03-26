"""
Windows Build Script for BadApp3
Run this on a Windows machine with Python installed

Usage:
    python build_windows.py
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_exe():
    """Build Windows executable"""
    print("Building Windows executable...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=BadApp3",
        "--windowed",
        "--onefile",
        "--exclude-module=build_windows",
        "--exclude-module=setup",
        "--noconfirm",  # Overwrite without asking
        "main.py",
    ]

    subprocess.check_call(cmd)

    exe_path = Path("dist") / "BadApp3.exe"
    if not exe_path.exists():
        raise FileNotFoundError(
            "Build command finished, but dist\\BadApp3.exe was not found. "
            "Check antivirus quarantine and PyInstaller output for errors."
        )

    print("\n✅ Build complete!")
    print(f"Executable location: {os.path.join('dist', 'BadApp3.exe')}")


if __name__ == "__main__":
    print("=" * 50)
    print("BadApp3 Windows Build Script")
    print("=" * 50)

    if os.name != "nt":
        print("❌ Windows EXE build must be run on Windows.")
        print("Run this script from Command Prompt or PowerShell on a Windows PC.")
        sys.exit(1)

    try:
        install_requirements()
        build_exe()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
