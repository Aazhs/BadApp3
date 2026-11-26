# Build Screen Assistant

Build on the operating system you intend to distribute to. The packaged app uses the Codex CLI installed on the user's computer. Follow the [account setup in the README](README.md#connect-your-chatgpt-account) before launching it.

## Windows

With a recent [Python installation](https://www.python.org/downloads/) that includes Tk, run these commands from the project directory in Command Prompt.

```cmd
py -3 -m venv venv
venv\Scripts\activate.bat
python build_windows.py
```

The output is `dist\BadApp3.exe`. If the build fails, check the PyInstaller output and `build\BadApp3\warn-BadApp3.txt`.

The [Windows build workflow](https://github.com/Aazhs/BadApp3/actions/workflows/windows.yml) also builds the x64 executable on pushes to `main`. It runs the test suite, checks native Codex discovery and screen capture, then launches the packaged GUI before uploading the executable as an artifact.

## macOS

Use a Python installation with Tk support.

```bash
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --name BadApp3 --windowed --collect-data customtkinter main.py
hdiutil create -volname "BadApp3" -srcfolder dist/BadApp3.app -ov -format UDZO BadApp3.dmg
```

The outputs are `dist/BadApp3.app` and `BadApp3.dmg`. Grant Screen Recording permission to the packaged app to use screenshot capture.
