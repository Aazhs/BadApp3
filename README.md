# Screen Assistant

Capture a screen region or attach images, then ask ChatGPT about what you see. Screen Assistant uses your signed-in Codex CLI and sends the images directly to the model. You can also ask a text-only question.

## Connect your ChatGPT account

Install or update the [Codex CLI](https://developers.openai.com/codex/cli/), then run the following in your terminal. Sign in with the ChatGPT account that has your subscription.

```bash
codex login
codex login status
```

The app reuses that sign-in. Requests use your plan's Codex allowance and any applicable credits. [Codex plan and usage details](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## Run on macOS or Linux

Use a Python installation with Tk support. On macOS, the python.org installer includes Tk. With Homebrew, install the matching `python-tk` formula for your Python version. On Linux, you may need to install your distribution's Tkinter package.

```bash
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On macOS, grant Screen Recording permission to the app that launches Python if screen capture fails. You can find the permission under **System Settings → Privacy & Security → Screen & System Audio Recording**. Reopen the app after granting access.

## Run on Windows

1. Install the [Windows Codex CLI](https://github.com/openai/codex#installing-and-running-codex-cli), then run `codex login` in PowerShell and choose ChatGPT sign-in.
2. Open the latest successful [Windows build](https://github.com/Aazhs/BadApp3/actions/workflows/windows.yml). Download **Screen-Assistant-Windows-x64** under **Artifacts**, extract it, and open `BadApp3.exe`.
3. When the app shows **ChatGPT connected**, click **Choose area**, then use **Capture & answer**.

The executable is built on Windows x64. It finds the standalone and npm Codex installations automatically. For a custom installation, set `CODEX_BIN` to the full path to `codex.exe` and reopen the app.

To run from source in Command Prompt, use a Python installation that includes Tk.

```cmd
py -3 -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python main.py
```

## Ask about your screen

1. Click **Choose area** and drag over the part of the screen you want to reuse.
2. Click **Capture & answer** whenever a new question appears there. The app sends the fresh crop with any question you typed and shows the answer automatically. If you click **Capture & answer** before choosing an area, releasing the drag sends the first capture.
3. Use **View capture** to check the last screenshot, **Stop** to cancel a request, or **Copy answer** to keep the result. **Clear session** clears the question, images, and answer while keeping your selected area.

For a text-only question or up to six saved images, use **Add images…** as needed and click **Ask ChatGPT**. You can also press **Cmd+Enter** on macOS or **Ctrl+Enter** on Windows and Linux. Click a thumbnail to inspect an attachment or use **×** to remove it.

The app hides during capture. Screen selection targets the primary display on macOS and Windows. Each request starts a fresh Codex session.

| Model | Reasoning |
| --- | --- |
| GPT-6 Luna · Quick | Default for short answers to straightforward questions |
| GPT-6.2 Sol · Light | Light reasoning for more involved questions |
| GPT-6.2 Sol · Medium | More time to reason through a question |
| GPT-6.2 Astra · High | Deeper reasoning when your plan offers Astra access |

These presets use standard service speed and vary the reasoning effort. [Codex model guidance](https://learn.chatgpt.com/docs/models)

## Troubleshoot the connection

- If the connection button says **Set up ChatGPT**, click it to see the sign-in status. After you sign in, click **Check again**.
- If a model is unavailable, update the CLI and try a Sol preset. Model availability depends on your account and workspace.
- If your plan is near its Codex usage limit, check your usage in ChatGPT or Codex. Attachments and deeper reasoning can use more of your allowance.

## Build and test

See [Build instructions](BUILD_INSTRUCTIONS.md) for packaging on Windows and macOS.

```bash
python -m py_compile main.py functions.py build_windows.py
python -m unittest -v
```
