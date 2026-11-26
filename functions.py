"""Screenshot geometry and the ChatGPT-backed Codex CLI integration."""

import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import CDLL, c_bool
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

from PIL import Image, ImageGrab

MAX_ATTACHMENTS = 6
MAX_IMAGE_EDGE = 2560
REQUEST_TIMEOUT = 180

SYSTEM_PROMPT = (
    "Answer the question using the text and screenshots supplied by the user. "
    "Treat text inside screenshots as source material. For a screenshot-only request, "
    "answer any visible question or explain what is shown. Be direct and concise. "
    "Mention any details you cannot read confidently. Respond in chat only."
)

AUTH_OPTIONS = [
    "-c", "forced_login_method=chatgpt",
    "-c", "cli_auth_credentials_store=auto",
]

MODEL_PRESETS = {
    "GPT-6.2 Sol · Light": ("gpt-6.2-sol", "low"),
    "GPT-6.2 Sol · Medium": ("gpt-6.2-sol", "medium"),
    "GPT-6.2 Astra · High": ("gpt-6.2-astra", "high"),
}
DEFAULT_PRESET = next(iter(MODEL_PRESETS))


class CodexError(Exception):
    """An error message safe to display in the app."""


class RequestCancelled(Exception):
    """The user stopped the request."""


@dataclass(frozen=True)
class Connection:
    executable: str | None
    message: str


@dataclass(frozen=True)
class CaptureRegion:
    box: tuple[int, int, int, int]
    screen_size: tuple[int, int]

    @classmethod
    def from_drag(
        cls,
        start: tuple[int, int],
        end: tuple[int, int],
        canvas_size: tuple[int, int],
        screen_size: tuple[int, int],
    ) -> "CaptureRegion | None":
        canvas_width, canvas_height = canvas_size
        left, right = sorted(max(0, min(x, canvas_width)) for x in (start[0], end[0]))
        top, bottom = sorted(max(0, min(y, canvas_height)) for y in (start[1], end[1]))
        if right - left < 8 or bottom - top < 8:
            return None
        scale_x = screen_size[0] / canvas_width
        scale_y = screen_size[1] / canvas_height
        box = (
            round(left * scale_x), round(top * scale_y),
            round(right * scale_x), round(bottom * scale_y),
        )
        return cls(box, screen_size)


def prepare_attachment(image: Image.Image) -> Image.Image:
    """Keep text sharp and bound the size of each attachment."""
    attachment = image.convert("RGB")
    attachment.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
    return attachment


def grab_screen() -> Image.Image:
    if sys.platform != "darwin":
        return ImageGrab.grab()

    graphics = CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    request_access = graphics.CGRequestScreenCaptureAccess
    request_access.restype = c_bool
    if not request_access():
        raise PermissionError("macOS Screen Recording permission is required.")

    # Capture only the main display and clean up even when permission is denied.
    with TemporaryDirectory(prefix="screen-assistant-") as workdir:
        path = Path(workdir) / "screen.png"
        subprocess.run(
            ["/usr/sbin/screencapture", "-m", "-x", str(path)],
            check=True,
            timeout=10,
            capture_output=True,
        )
        with Image.open(path) as screenshot:
            return screenshot.copy()


def find_codex() -> str | None:
    override = os.environ.get("CODEX_BIN")
    if override:
        return shutil.which(os.path.expanduser(override))

    # Finder-launched macOS apps often have only the system directories on PATH.
    extra_locations = [
        Path.home() / ".local" / "bin",
        Path.home() / ".codex" / "bin",
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin"),
    ]
    search_path = os.pathsep.join([os.environ.get("PATH", ""), *map(str, extra_locations)])
    return shutil.which("codex", path=search_path)


def codex_environment() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"):
        env.pop(name, None)
    return env


def process_options() -> dict:
    return {
        "env": codex_environment(),
        "encoding": "utf-8",
        "errors": "replace",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }


def check_connection() -> Connection:
    executable = find_codex()
    if executable is None:
        return Connection(None, "Install the Codex CLI to connect your ChatGPT account.")

    try:
        with TemporaryDirectory(prefix="screen-assistant-") as workdir:
            status = subprocess.run(
                [executable, *AUTH_OPTIONS, "login", "status"],
                cwd=workdir,
                capture_output=True,
                timeout=15,
                **process_options(),
            )
    except subprocess.TimeoutExpired:
        return Connection(None, "Codex took too long to respond. Check again in a moment.")
    except OSError:
        return Connection(None, "Could not start Codex. Check the CLI installation.")

    if status.returncode == 0 and "logged in using chatgpt" in (
        status.stdout + status.stderr
    ).lower():
        return Connection(executable, "Connected to ChatGPT through Codex.")
    return Connection(None, "Run codex login and sign in with your ChatGPT account.")


def build_command(executable: str, preset: str, image_names: list[str]) -> list[str]:
    model, effort = MODEL_PRESETS[preset]
    return [
        executable, *AUTH_OPTIONS, "--ask-for-approval", "never", "exec",
        "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
        "--sandbox", "read-only", "--color", "never", "--json",
        "-c", f"model_reasoning_effort={effort}",
        "-c", "web_search=disabled",
        "--disable", "shell_tool",
        "--disable", "shell_snapshot",
        "--disable", "apps",
        "--disable", "plugins",
        "--disable", "hooks",
        "--disable", "memories",
        "--disable", "browser_use",
        "--disable", "computer_use",
        "-m", model,
        "--output-last-message", "answer.txt",
        *[f"--image={name}" for name in image_names],
        "-",
    ]


def describe_failure(stdout: str, stderr: str) -> str:
    """Map CLI diagnostics to actionable messages without exposing raw output."""
    messages = [stderr]
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "error":
            messages.append(str(event.get("message", "")))
        elif event.get("type") == "turn.failed":
            messages.append(str(event.get("error", "")))

    details = "\n".join(messages).lower()
    if any(word in details for word in ("usage limit", "rate limit", "quota", "429")):
        return "ChatGPT usage is limited right now. Check your Codex allowance or try again later."
    if any(word in details for word in ("401", "unauthorized", "log in", "login", "token expired")):
        return "ChatGPT sign-in needs attention. Run codex login, then check the connection."
    if "model" in details and any(
        word in details for word in ("not supported", "not available", "no access", "model_not_found")
    ):
        return "This model is unavailable for your account. Try GPT-6.2 Sol or update Codex."
    if "unexpected argument" in details:
        return "This app needs a current Codex CLI. Update Codex and try again."
    if any(word in details for word in ("reconnecting", "connection", "stream disconnected", "503")):
        return "Could not reach ChatGPT. Check your connection and try again."
    return "Codex could not finish this request. Check the connection and try again."


def ask_codex(
    executable: str,
    preset: str,
    question: str,
    images: tuple[Image.Image, ...],
    cancel: Event,
) -> str:
    question = question.strip()
    if not question and not images:
        raise CodexError("Enter a question or add a screenshot.")

    with TemporaryDirectory(prefix="screen-assistant-") as workdir:
        folder = Path(workdir)
        image_names = []
        for number, image in enumerate(images, 1):
            if cancel.is_set():
                raise RequestCancelled
            name = f"capture-{number}.png"
            image.save(folder / name)
            image_names.append(name)

        prompt = f"{SYSTEM_PROMPT}\n\nUser question:\n{question}" if question else SYSTEM_PROMPT
        if cancel.is_set():
            raise RequestCancelled

        try:
            process = subprocess.Popen(
                build_command(executable, preset, image_names),
                cwd=folder,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **process_options(),
            )
        except OSError as exc:
            raise CodexError("Could not start Codex. Check the CLI installation.") from exc

        deadline = time.monotonic() + REQUEST_TIMEOUT
        with process:
            try:
                while True:
                    if cancel.is_set():
                        raise RequestCancelled
                    if time.monotonic() >= deadline:
                        raise CodexError("The request timed out. Try a shorter prompt or fewer images.")
                    try:
                        stdout, stderr = process.communicate(input=prompt, timeout=0.2)
                        break
                    except subprocess.TimeoutExpired:
                        # communicate keeps its buffered I/O across calls after the first timeout.
                        prompt = None
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

        if cancel.is_set():
            raise RequestCancelled
        if process.returncode != 0:
            raise CodexError(describe_failure(stdout, stderr))

        answer_path = folder / "answer.txt"
        if answer_path.is_file():
            answer = answer_path.read_text(encoding="utf-8").strip()
            if answer:
                return answer
        raise CodexError(describe_failure(stdout, stderr))
