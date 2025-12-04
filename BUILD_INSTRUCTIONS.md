# Build Instructions for BadApp2

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
   - The EXE file will be in: `dist\BadApp2.exe`

### Alternative: Manual Build

If the script doesn't work, build manually:

```cmd
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
pyinstaller --name=BadApp2 --windowed --onefile main.py
```

### Important Notes

- **Tesseract**: Users need to install Tesseract OCR separately
- **API Key**: Users will need their own GitHub API token
- **First Run**: Windows may show a security warning (click "More info" → "Run anyway")

## Building on macOS (Already Complete)

The macOS build has been completed:
- App: `dist/BadApp2.app`
- DMG: `BadApp2.dmg`

To rebuild:
```bash
/Users/aarsh/Codes/badApp2/venv/bin/pyinstaller --name="BadApp2" --windowed --onefile main.py
hdiutil create -volname "BadApp2" -srcfolder dist/BadApp2.app -ov -format UDZO BadApp2.dmg
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
