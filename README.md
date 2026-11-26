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

```cmd
py -3 -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python main.py
```

Run the Windows version of the Codex CLI so Screen Assistant can find it. If the app cannot find Codex, make sure `codex` is on your PATH or set `CODEX_BIN` to the full path to the CLI executable before launching.

## Ask about your screen

1. Click **Capture** and drag over an area. Future captures reuse that area. Use **Choose area** to change it or **Add images…** to attach saved files.
2. Click a thumbnail to inspect it or use **×** to remove it. Up to six images can go in a request.
3. Type a question, or leave it empty to ask about the screenshots. Click **Ask ChatGPT** or press **Cmd+Enter** on macOS or **Ctrl+Enter** on Windows and Linux.
4. Use **Stop** to stop an in-progress request and **Copy answer** to keep the result. **Clear session** removes the question, images, and answer while keeping your selected capture area.

The app hides during capture. Screen selection targets the primary display on macOS and Windows. When you click **Ask ChatGPT**, the app sends the question and currently attached images through Codex. Each request starts a fresh Codex session.

| Model | Reasoning |
| --- | --- |
| GPT-6.2 Sol · Light | Default for quick screenshot and text questions |
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
