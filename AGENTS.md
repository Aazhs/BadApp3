# AGENTS.md
Agent-facing guidance for this repository.

## Repository Overview
- Language: Python
- App type: desktop GUI
- UI library: `customtkinter`
- Screenshot capture: Pillow and macOS `screencapture`
- Model access: Codex CLI with ChatGPT sign-in and native image attachments
- Entrypoint: `main.py`
- Core helpers: `functions.py`
- Build files: `build_windows.py`, `setup.py`, `BUILD_INSTRUCTIONS.md`

## Cursor/Copilot Rules
Checked for:
- `.cursorrules`
- `.cursor/rules/`
- `.github/copilot-instructions.md`
Status:
- No Cursor or Copilot rule files exist in the current repository.
- If these appear later, treat them as higher-priority behavior constraints.

## Environment Setup
Preferred setup:
```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
codex login
```
Helper scripts:
- `activate_venv.sh` activates `venv`.
- `startup.sh` creates `venv` but activation is safer done manually.
Security:
- Never commit API keys or tokens.

## Run Commands
Run app:
```bash
python main.py
```
Alternative:
```bash
venv/bin/python main.py
```

## Build Commands
Windows EXE (preferred):
```bash
python build_windows.py
```
Windows EXE (manual):
```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name=BadApp3 --windowed --onefile --collect-data customtkinter main.py
```
macOS app + dmg:
```bash
venv/bin/pyinstaller --name="BadApp3" --windowed --collect-data customtkinter main.py
hdiutil create -volname "BadApp3" -srcfolder dist/BadApp3.app -ov -format UDZO BadApp3.dmg
```

## Lint / Static Checks
Current state:
- No committed linter config (`ruff`, `flake8`, `pylint`, `black` not configured).
Minimum syntax/static check before merge:
```bash
python -m py_compile main.py functions.py build_windows.py
```
If linting is introduced in a PR:
- Prefer `ruff` for lint/import ordering.
- Prefer `black` for formatting.
- Do not mass-reformat unrelated files unless requested.

## Test Commands
Run the standard library test suite:
```bash
python -m unittest -v
python -m unittest test.CaptureRegionTests.test_retina_drag_maps_to_image_pixels
```

## Code Style Guidelines

### Imports
- Group imports: standard library, third-party, local.
- Keep imports explicit; avoid wildcard imports.
- Prefer one import per line when practical.
- Remove unused imports in touched files.

### Formatting
- Follow PEP 8.
- Use 4 spaces; never tabs.
- Target line width around 88-100 chars.
- Keep functions focused and readable.
- Avoid unrelated formatting-only edits.

### Types
- Add type hints to new/changed functions when practical.
- Use concrete collection types when known (`list[str]`, `dict[str, int]`).
- For GUI widget args, use concrete widget types or `Any`.
- Prefer simple, maintainable typing.

### Naming
- Use `snake_case` for vars/functions.
- Use `UPPER_SNAKE_CASE` for constants.
- Prefer descriptive names (`screenshot_count`, `api_client`).
- Callback names should be verb-first (`set_api_key`).

### Error Handling
- Never silently swallow exceptions.
- Catch specific exceptions when feasible.
- Broad `except Exception` is acceptable only at UI/app boundaries.
- Show user-safe error text in the UI.
- Keep technical details in logs/debug output.
- Validate preconditions early (ChatGPT sign-in, question or attachments available).

### State Management
- Minimize module-level mutable globals.
- Prefer explicit state passing or a small state class when refactoring.
- If globals are modified, keep transitions obvious and documented.

### API and Secrets
- Keep endpoint/model constants centralized.
- Never hardcode secrets.
- Never log full tokens.
- Add timeout/retry behavior for new network calls.

### UI Conventions
- Keep labels/messages clear and action-oriented.
- Update status labels immediately when state changes.
- Keep UI callbacks thin; move logic into helpers.
- Preserve current textbox pattern (disabled except while writing).

## Change Hygiene
- Keep edits scoped to the user request.
- Avoid unnecessary file moves/renames.
- Update docs when behavior or commands change.
- If adding tests/lint tooling, update this file with exact commands.

## Pre-PR Checklist
- Run `python -m py_compile main.py functions.py build_windows.py`.
- Run available tests (or add focused tests for changed behavior).
- Smoke test UI-impacting changes with `python main.py`.
- Ensure no secrets are committed.
- Confirm docs still match repository behavior.
