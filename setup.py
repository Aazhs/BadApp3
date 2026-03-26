from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    "packages": ["customtkinter", "PIL", "pyautogui", "pytesseract", "mistralai"],
    "iconfile": None,  # Add path to .icns file if you have one
    "plist": {
        "CFBundleName": "BadApp3",
        "CFBundleDisplayName": "BadApp3",
        "CFBundleIdentifier": "com.badapp3.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
