# BadApp3

Desktop Python app that captures screenshots, extracts text with OCR, and sends it to GitHub Models.

## Run

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Windows Prerequisites

- Install Tesseract OCR (required for screenshot text extraction):
  `https://github.com/UB-Mannheim/tesseract/wiki`
- During install, keep default path (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
- Restart this app after installing Tesseract.
- If OCR returns empty or errors, verify `tesseract --version` works in Command Prompt.

## GitHub Models API Key (Beginner-Friendly Guide)

This app uses GitHub Models (`https://models.github.ai/inference`) and needs a GitHub Personal Access Token (PAT).

### Quick Links

- Token settings: `https://github.com/settings/tokens`
- PAT docs: `https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens`
- GitHub Models docs: `https://docs.github.com/en/github-models/prototyping-with-ai-models`
- Models marketplace: `https://github.com/marketplace/models`

### Step-by-Step

1. Sign in to your GitHub account.
2. Open token settings: `https://github.com/settings/tokens`.
3. Choose one token type:
   - **Fine-grained token** (recommended for beginners)
   - **Tokens (classic)**
4. Click **Generate new token**.
5. Add a token name (example: `BadApp3 Token`).
6. Set an expiration date.
7. Enable model permission: `models:read`.
8. Click **Generate token**.
9. Copy the token immediately (GitHub may not show it fully again).
10. In this app, paste it into **GitHub API key** and click **Connect**.

### If Something Fails

- **Invalid key**: Create a new token and ensure `models:read` is enabled.
- **Rate limit reached**: Switch model to `openai/gpt-4.1-mini` or `openai/gpt-4o-mini`.
- **Still stuck**: Open the docs links above and compare each step.

### Plan Notes

- GitHub Free users can still use GitHub Models with free-rate limits.
- GitHub Pro / Pro Education users typically get better limits for some model tiers.

## Suggested Models

- Default: `openai/gpt-4.1-mini`
- Alternative fast/cheap: `openai/gpt-4o-mini`
- Open model option: `meta/llama-3.3-70b-instruct`

## Build

Windows:

```bash
python build_windows.py
```

macOS:

```bash
venv/bin/pyinstaller --name="BadApp3" --windowed --onefile main.py
```
