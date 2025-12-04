"""
Windows Build Script for BadApp2
Run this on a Windows machine with Python installed

Usage:
    python build_windows.py
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe():
    """Build Windows executable"""
    print("Building Windows executable...")
    
    cmd = [
        "pyinstaller",
        "--name=BadApp2",
        "--windowed",
        "--onefile",
        "--icon=icon.ico",  # Optional: add if you have an icon
        "main.py"
    ]
    
    subprocess.check_call(cmd)
    print("\n✅ Build complete!")
    print(f"Executable location: {os.path.join('dist', 'BadApp2.exe')}")

if __name__ == "__main__":
    print("=" * 50)
    print("BadApp2 Windows Build Script")
    print("=" * 50)
    
    try:
        install_requirements()
        build_exe()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
