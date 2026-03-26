import os
import shutil

import pyautogui
import pytesseract
from mistralai import Mistral, SystemMessage, UserMessage

API_ENDPOINT = "https://models.github.ai/inference"

# Better default than mistral-small for quality/speed on GitHub Models.
DEFAULT_MODEL = "openai/gpt-4.1-mini"

# Common GitHub Models choices available to most users.
AVAILABLE_MODELS = [
    "openai/gpt-4.1-mini",
    "openai/gpt-4o-mini",
    "meta/llama-3.3-70b-instruct",
    "mistral-ai/mistral-small-2503",
]

SYSTEM_PROMPT = (
    "You are a helpful assistant. The user text comes from OCR screenshots. "
    "Fix obvious OCR mistakes mentally, then answer clearly. "
    "If it is a coding question, provide only the working code no explaination, And code should be in Python Language, return simple code"
)

final_input = []
final_string = ""
api_response = ""
client = None
selected_model = DEFAULT_MODEL
selected_region = None


def _configure_tesseract_cmd():
    if os.name != "nt":
        return

    if shutil.which("tesseract"):
        return

    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return


_configure_tesseract_cmd()


def get_available_models():
    return AVAILABLE_MODELS.copy()


def get_selected_model():
    return selected_model


def set_model(model_name):
    global selected_model
    if model_name in AVAILABLE_MODELS:
        selected_model = model_name


def get_image_count():
    return len(final_input)


def get_selected_region():
    return selected_region


def set_selected_region(region):
    global selected_region
    selected_region = region


def clear_selected_region():
    global selected_region
    selected_region = None


def take_ss():
    if selected_region is None:
        screenshot = pyautogui.screenshot()
    else:
        screenshot = pyautogui.screenshot(region=selected_region)
    final_input.append(screenshot)


def show_final():
    for img in final_input:
        img.show()


def _write_result(result_textbox, message):
    result_textbox.configure(state="normal")
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", message)
    result_textbox.configure(state="disabled")


def restart_ss(result_textbox):
    global final_string
    final_input.clear()
    final_string = ""
    _write_result(result_textbox, "AI response will appear here...")


def img_to_txt():
    global final_string
    final_string = ""
    for image in final_input:
        final_string += pytesseract.image_to_string(image)


def _sanitize_api_key(raw_value):
    cleaned = raw_value.strip()
    if not cleaned:
        return ""

    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned[7:].strip()

    if "```" in cleaned:
        lines = []
        for line in cleaned.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("```"):
                continue
            lines.append(stripped)
        if lines:
            cleaned = lines[0]

    if "\n" in cleaned or "\r" in cleaned:
        cleaned = cleaned.splitlines()[0].strip()

    if " " in cleaned or "\t" in cleaned:
        parts = [part.strip() for part in cleaned.split() if part.strip()]
        cleaned = parts[0] if parts else ""

    return cleaned


def _looks_like_github_token(token):
    token_prefixes = ("github_pat_", "ghp_", "gho_", "ghu_", "ghs_", "ghr_")
    return token.startswith(token_prefixes) and len(token) >= 20


def initialize_client(api_key):
    global client
    cleaned_key = _sanitize_api_key(api_key)
    if not cleaned_key:
        return False, "Please enter a valid API key."

    if not _looks_like_github_token(cleaned_key):
        return (
            False,
            "This does not look like a GitHub token. Paste only the PAT value (no 'Bearer', no code block).",
        )

    try:
        client = Mistral(api_key=cleaned_key, server_url=API_ENDPOINT)
    except Exception as exc:
        return False, f"Could not initialize API client: {exc}"

    return True, "API key connected to GitHub Models."


def send_to_api(result_textbox):
    global api_response

    if client is None:
        _write_result(result_textbox, "Error: API key not set. Add your key first.")
        return False

    if not final_input:
        _write_result(result_textbox, "No screenshots captured yet.")
        return False

    try:
        img_to_txt()
    except pytesseract.TesseractNotFoundError:
        _write_result(
            result_textbox,
            "OCR Error: Tesseract is not installed or not found. On Windows, install it from "
            "https://github.com/UB-Mannheim/tesseract/wiki and restart the app.",
        )
        return False
    except Exception as exc:
        _write_result(result_textbox, f"OCR Error: {exc}")
        return False

    if not final_string.strip():
        _write_result(
            result_textbox, "OCR found no readable text in current screenshots."
        )
        return False

    _write_result(result_textbox, "Thinking...")

    try:
        response = client.chat.complete(
            model=selected_model,
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                UserMessage(content=final_string),
            ],
            temperature=0.3,
            max_tokens=1200,
            top_p=1.0,
        )
        api_response = response.choices[0].message.content
        _write_result(result_textbox, api_response)
        return True
    except Exception as exc:
        _write_result(result_textbox, f"API Error: {exc}")
        return False
