# Build Instructions for BadApp3

## Building on Windows

### Prerequisites
1. Install Python 3.13 or later from [python.org](https://www.python.org/downloads/)
2. Install Tesseract OCR from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Download and install the Windows installer
   - Add Tesseract to PATH or note the installation directory

### Steps to Build Windows EXE

1. **Transfer files to Windows machine**
   - Copy all project files to your Windows computer

2. **Open Command Prompt or PowerShell**
   ```cmd
   cd path\to\badApp2
   ```

3. **Run the build script**
   ```cmd
   python build_windows.py
   ```

4. **Find your executable**
   - The EXE file will be in: `dist\BadApp3.exe`

### If `.exe` is not generated

1. Confirm you are building on Windows (not macOS/Linux).
2. Run from the project root (same folder as `main.py`).
3. Use Python launcher explicitly:
   ```cmd
   py -3 -m venv venv
   venv\Scripts\activate
   py -3 -m pip install -r requirements.txt
   py -3 -m pip install pyinstaller
   py -3 -m PyInstaller --name=BadApp3 --windowed --onefile main.py
   ```
4. Check whether antivirus quarantined the file in `dist\BadApp3.exe`.
5. If build logs show errors, open and share `build\BadApp3\warn-BadApp3.txt`.

### Alternative: Manual Build

If the script doesn't work, build manually:

```cmd
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
pyinstaller --name=BadApp3 --windowed --onefile main.py
```

### Important Notes

- **Tesseract**: Users need to install Tesseract OCR separately
- **API Key**: Users will need their own GitHub API token
- **First Run**: Windows may show a security warning (click "More info" → "Run anyway")

## Building on macOS (Already Complete)

The macOS build has been completed:
- App: `dist/BadApp3.app`
- DMG: `BadApp3.dmg`

To rebuild:
```bash
/Users/aarsh/Codes/badApp2/venv/bin/pyinstaller --name="BadApp3" --windowed --onefile main.py
hdiutil create -volname "BadApp3" -srcfolder dist/BadApp3.app -ov -format UDZO BadApp3.dmg
```

## Cross-Platform Notes

This app requires:
1. **Python packages**: Installed automatically during build
2. **Tesseract OCR**: Must be installed separately by end users
3. **API Key**: GitHub API token for Mistral AI

### Tesseract Installation Links
- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`
