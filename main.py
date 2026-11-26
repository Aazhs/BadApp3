"""Desktop workspace for asking ChatGPT about screenshots."""

import logging
import sys
import tkinter as tk
import webbrowser
from queue import Empty, Queue
from subprocess import SubprocessError
from threading import Event, Thread
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageOps, ImageTk

from functions import (
    DEFAULT_PRESET,
    MAX_ATTACHMENTS,
    MODEL_PRESETS,
    CaptureRegion,
    CodexError,
    Connection,
    RequestCancelled,
    ask_codex,
    check_connection,
    grab_screen,
    prepare_attachment,
)

BACKGROUND = ("#eef1f5", "#141920")
CARD = ("#ffffff", "#1d252f")
FIELD = ("#f2f5f8", "#151c25")
BORDER = ("#dce4ec", "#303c49")
TEXT = ("#192331", "#ecf1f6")
MUTED = ("#4f6072", "#a0afbf")
BUTTON = ("#e7edf4", "#2b3745")
HOVER = ("#d7e2ef", "#394a5d")
ACCENT = ("#206253", "#246b59")
ACCENT_HOVER = ("#185247", "#2b7b67")
SUCCESS = ("#17604d", "#8cdbc0")
ERROR = ("#a6313a", "#ffabb1")
INSTALL_URL = "https://developers.openai.com/codex/cli/"
CAPTURE_QUESTION = (
    "Answer the question shown in the screenshot. Start with the answer and keep it short. "
    "For multiple choice, give the option and its text."
)
LOG = logging.getLogger(__name__)


class RegionSelector(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        screenshot: Image.Image,
        on_done: Callable[[CaptureRegion | None], None],
    ) -> None:
        super().__init__(parent)
        self.withdraw()
        self.screenshot = screenshot
        self.on_done = on_done
        self.start: tuple[int, int] | None = None
        self.outline: int | None = None

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+0+0")
        self.canvas = tk.Canvas(self, cursor="cross", highlightthickness=0, bg="#111920")
        self.canvas.pack(fill="both", expand=True)
        self.background = self.canvas.create_image(0, 0, anchor="nw")
        self.photo: ImageTk.PhotoImage | None = None
        self.canvas.bind("<Configure>", self.draw_screen)
        self.canvas.bind("<ButtonPress-1>", self.begin_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        self.bind("<Escape>", lambda _event: self.finish(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self.finish(None))
        self.deiconify()
        self.focus_force()

    def draw_screen(self, event: tk.Event) -> None:
        image = self.screenshot.resize((event.width, event.height), Image.Resampling.BILINEAR)
        self.photo = ImageTk.PhotoImage(image, master=self)
        self.canvas.itemconfigure(self.background, image=self.photo)
        self.canvas.delete("hint")
        hint = self.canvas.create_text(
            24, 42, anchor="nw", fill="#ffffff", font=("TkDefaultFont", 13),
            text="Drag to select an area  ·  Esc to cancel", tags="hint",
        )
        left, top, right, bottom = self.canvas.bbox(hint)
        backdrop = self.canvas.create_rectangle(
            left - 9, top - 6, right + 9, bottom + 6, fill="#141920", width=0, tags="hint"
        )
        self.canvas.tag_lower(backdrop, hint)

    def begin_drag(self, event: tk.Event) -> None:
        self.start = (event.x, event.y)
        if self.outline is not None:
            self.canvas.delete(self.outline)
        self.outline = self.canvas.create_rectangle(
            *self.start, *self.start, outline="#68e5bc", width=3
        )

    def drag(self, event: tk.Event) -> None:
        if self.start is not None:
            self.canvas.coords(self.outline, *self.start, event.x, event.y)

    def end_drag(self, event: tk.Event) -> None:
        if self.start is None:
            return
        region = CaptureRegion.from_drag(
            self.start,
            (event.x, event.y),
            (self.canvas.winfo_width(), self.canvas.winfo_height()),
            self.screenshot.size,
        )
        self.finish(region)

    def finish(self, region: CaptureRegion | None) -> None:
        self.destroy()
        self.on_done(region)


class ScreenAssistant(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=BACKGROUND)
        self.title("Screen Assistant")
        self.geometry("690x775")
        self.minsize(580, 650)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.region: CaptureRegion | None = None
        self.latest_capture: Image.Image | None = None
        self.images: list[Image.Image] = []
        self.connection = Connection(None, "Checking for a ChatGPT sign-in through Codex…")
        self.events: Queue = Queue()
        self.cancel: Event | None = None
        self.checking_connection = False
        self.closing = False
        self.capturing = False
        self.answer = ""
        self.setup: ctk.CTkToplevel | None = None
        self.setup_status: ctk.CTkLabel | None = None
        self.check_button: ctk.CTkButton | None = None
        self.preview: ctk.CTkToplevel | None = None

        self.build_workspace()
        modifier = "Command" if sys.platform == "darwin" else "Control"
        self.bind(f"<{modifier}-Return>", self.ask_shortcut)
        self.bind("<Control-Shift-S>", self.capture_shortcut)
        if modifier == "Command":
            self.bind("<Command-Shift-s>", self.capture_shortcut)
        self.after(60, self.poll_events)
        self.refresh_connection()

    @staticmethod
    def button(parent, text: str, command: Callable, **kwargs) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent, text=text, command=command, height=32, corner_radius=8,
            fg_color=BUTTON, hover_color=HOVER, text_color=TEXT, **kwargs,
        )

    @staticmethod
    def label(parent, text: str = "", size: int = 13, bold: bool = False, **kwargs):
        return ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"),
            **kwargs,
        )

    def card(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def build_workspace(self) -> None:
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=22, pady=(16, 12))
        header = ctk.CTkFrame(workspace, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))
        self.label(header, "Screen Assistant", size=29, bold=True, text_color=TEXT).pack(side="left")
        self.account_button = self.button(header, "Checking ChatGPT…", self.show_setup, width=142)
        self.account_button.pack(side="right")

        context = self.card(workspace)
        context_header = ctk.CTkFrame(context, fg_color="transparent")
        context_header.pack(fill="x", padx=14, pady=(9, 2))
        self.label(context_header, "Screenshots", size=16, bold=True, text_color=TEXT).pack(
            side="left"
        )
        self.pin = ctk.CTkCheckBox(
            context_header, text="Keep on top", command=self.update_pin,
            width=110, checkbox_width=17, checkbox_height=17,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=MUTED,
        )
        self.pin.pack(side="right")

        capture_controls = ctk.CTkFrame(context, fg_color="transparent")
        capture_controls.pack(fill="x", padx=14, pady=(2, 0))
        self.capture_button = ctk.CTkButton(
            capture_controls, text="Capture & answer", command=self.capture, width=137, height=32,
            corner_radius=8, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#ffffff",
            state="disabled",
        )
        self.capture_button.pack(side="left", padx=(0, 7))
        self.area_button = self.button(
            capture_controls, "Choose area", lambda: self.capture(choose_area=True), width=102
        )
        self.area_button.pack(side="left", padx=(0, 7))
        self.add_button = self.button(capture_controls, "Add images…", self.add_images, width=106)
        self.add_button.pack(side="left")
        self.attachment_count = self.label(capture_controls, text_color=MUTED)
        self.attachment_count.pack(side="right")

        self.region_label = self.label(context, text_color=MUTED)
        self.region_label.pack(anchor="w", padx=14, pady=(4, 0))
        self.attachment_row = ctk.CTkFrame(context, height=69, fg_color=FIELD, corner_radius=8)
        self.attachment_row.pack(fill="x", padx=14, pady=(3, 12))
        self.attachment_row.pack_propagate(False)
        self.update_region_label()
        self.update_attachments()

        composer = self.card(workspace)
        question_header = ctk.CTkFrame(composer, fg_color="transparent")
        question_header.pack(fill="x", padx=14, pady=(8, 2))
        self.label(question_header, "Question", size=16, bold=True, text_color=TEXT).pack(
            side="left"
        )
        self.label(question_header, "Optional with screenshots", text_color=MUTED).pack(
            side="right"
        )
        self.question = ctk.CTkTextbox(
            composer, height=66, wrap="word", fg_color=FIELD, text_color=TEXT,
            border_width=1, border_color=BORDER, font=ctk.CTkFont(size=14),
        )
        self.question.pack(fill="x", padx=14)
        actions = ctk.CTkFrame(composer, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(8, 11))
        self.model_menu = ctk.CTkOptionMenu(
            actions, values=list(MODEL_PRESETS), width=185, height=32, corner_radius=8,
            fg_color=BUTTON, button_color=BUTTON, button_hover_color=HOVER, text_color=TEXT,
            dropdown_fg_color=CARD, dropdown_hover_color=HOVER, dropdown_text_color=TEXT,
            dynamic_resizing=False,
        )
        self.model_menu.set(DEFAULT_PRESET)
        self.model_menu.pack(side="left")
        self.ask_button = self.button(
            actions, "Ask ChatGPT", self.ask_or_stop, width=117, state="disabled",
        )
        self.ask_button.pack(side="right")

        footer = ctk.CTkFrame(workspace, fg_color="transparent")
        footer.pack(side="bottom", fill="x")
        shortcut = "⌘↵ to ask" if sys.platform == "darwin" else "Ctrl+Enter to ask"
        self.label(footer, shortcut, size=12, text_color=MUTED).pack(
            side="right", anchor="n", padx=(10, 0)
        )
        self.status = self.label(
            footer, "Checking ChatGPT connection…", size=12, text_color=MUTED,
            justify="left", anchor="w", wraplength=405,
        )
        self.status.pack(side="left", fill="x", expand=True, anchor="w")

        answer_card = ctk.CTkFrame(
            workspace, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER,
        )
        answer_card.pack(fill="both", expand=True, pady=(0, 5))
        answer_header = ctk.CTkFrame(answer_card, fg_color="transparent")
        answer_header.pack(fill="x", padx=14, pady=(8, 7))
        self.label(answer_header, "Answer", size=16, bold=True, text_color=TEXT).pack(side="left")
        self.copy_button = self.button(answer_header, "Copy answer", self.copy_answer, width=97)
        self.copy_button.pack(side="right")
        self.clear_button = self.button(
            answer_header, "Clear session", self.clear_session, width=98
        )
        self.clear_button.pack(side="right", padx=(0, 7))
        self.capture_preview_button = self.button(
            answer_header, "View capture", self.preview_latest_capture, width=97, state="disabled",
        )
        self.capture_preview_button.pack(side="right", padx=(0, 7))
        self.result = ctk.CTkTextbox(
            answer_card, height=100, wrap="word", fg_color=FIELD, text_color=TEXT,
            border_width=1, border_color=BORDER, font=ctk.CTkFont(size=14),
        )
        self.result.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.show_answer("")

    def set_status(self, message: str, color=MUTED) -> None:
        self.status.configure(text=message, text_color=color)

    def update_pin(self) -> None:
        self.attributes("-topmost", bool(self.pin.get()))

    def update_attachments(self) -> None:
        count = len(self.images)
        self.attachment_count.configure(text=f"{count} of {MAX_ATTACHMENTS} attached")
        self.add_button.configure(state="normal" if count < MAX_ATTACHMENTS else "disabled")

        for child in self.attachment_row.winfo_children():
            child.destroy()
        if not self.images:
            self.label(self.attachment_row, "No images attached", text_color=MUTED).pack(
                fill="both", expand=True
            )
            return

        for index, image in enumerate(self.images):
            thumbnail = ImageOps.contain(image, (46, 42))
            icon = ctk.CTkImage(thumbnail, size=thumbnail.size)
            tile = ctk.CTkFrame(self.attachment_row, fg_color="transparent")
            tile.pack(side="left", padx=(5, 0), pady=6)
            ctk.CTkButton(
                tile, text="", image=icon, command=lambda i=index: self.preview_image(i),
                width=50, height=54, fg_color=BUTTON, hover_color=HOVER, corner_radius=6,
            ).pack(side="left")
            ctk.CTkButton(
                tile, text="×", command=lambda i=index: self.remove_image(i),
                width=22, height=26, fg_color="transparent", hover_color=HOVER, text_color=TEXT,
            ).pack(side="left", anchor="n")

    def update_region_label(self) -> None:
        if self.region is None:
            self.region_label.configure(text="Choose an area to capture")
        else:
            left, top, right, bottom = self.region.box
            self.region_label.configure(text=f"Capture area  ·  {right - left} × {bottom - top} px")

    def capture_shortcut(self, _event: tk.Event) -> str:
        self.capture()
        return "break"

    def capture(self, choose_area: bool = False) -> None:
        if self.capturing or self.closing or self.cancel is not None:
            return
        if not choose_area and (not self.connection.executable or self.checking_connection):
            self.set_status(self.connection.message, ERROR)
            return
        if self.preview is not None and self.preview.winfo_exists():
            self.preview.destroy()
        self.capturing = True
        self.withdraw()
        self.after(230, self.capture_screen, choose_area)

    def capture_screen(self, choose_area: bool) -> None:
        try:
            screenshot = grab_screen()
        except (OSError, SubprocessError):
            LOG.exception("Screen capture failed")
            self.restore_window()
            message = "Could not capture the screen. Check your desktop capture permissions."
            if sys.platform == "darwin":
                message = "Allow Screen Recording for this app or Terminal in System Settings."
            self.set_status(message, ERROR)
            return

        if choose_area or self.region is None or self.region.screen_size != screenshot.size:
            RegionSelector(
                self, screenshot,
                lambda region: self.finish_capture(screenshot, region, ask=not choose_area),
            )
        else:
            self.finish_capture(screenshot, self.region)

    def restore_window(self) -> None:
        self.capturing = False
        self.deiconify()
        self.lift()
        self.update_pin()

    def finish_capture(
        self, screenshot: Image.Image, region: CaptureRegion | None, *, ask: bool = True
    ) -> None:
        self.restore_window()
        if region is None:
            self.set_status("Capture canceled.")
            return
        self.region = region
        self.update_region_label()
        if not ask:
            self.set_status("Area saved. Click Capture & answer when ready.", SUCCESS)
            return

        self.latest_capture = prepare_attachment(screenshot.crop(region.box))
        self.capture_preview_button.configure(state="normal")
        self.start_request((self.latest_capture,), default_question=CAPTURE_QUESTION)

    def add_images(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self, title="Attach images",
            filetypes=[("Images", ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")),
                       ("All files", "*")],
        )
        if not paths:
            return
        added = 0
        rejected = 0
        for path in paths:
            if len(self.images) == MAX_ATTACHMENTS:
                break
            try:
                with Image.open(path) as image:
                    self.images.append(prepare_attachment(ImageOps.exif_transpose(image)))
                added += 1
            except (OSError, Image.DecompressionBombError, ValueError):
                rejected += 1
                LOG.exception("Could not open attachment")
        self.update_attachments()
        if rejected or added < len(paths):
            self.set_status(f"Attached {added} of {len(paths)} selected images.", ERROR)
        else:
            self.set_status("Images attached." if added > 1 else "Image attached.", SUCCESS)

    def preview_image(self, index: int) -> None:
        self.show_image(self.images[index], f"Image {index + 1} of {len(self.images)}")

    def preview_latest_capture(self) -> None:
        if self.latest_capture is not None:
            self.show_image(self.latest_capture, "Latest capture")

    def show_image(self, image: Image.Image, title: str) -> None:
        if self.preview is not None and self.preview.winfo_exists():
            self.preview.destroy()
        window = ctk.CTkToplevel(self, fg_color=FIELD)
        self.preview = window
        window.title(title)
        window.transient(self)
        size = (round(self.winfo_screenwidth() * 0.85), round(self.winfo_screenheight() * 0.76))
        preview = ImageOps.contain(image, size)
        photo = ctk.CTkImage(preview, size=preview.size)
        self.label(window, image=photo).pack(padx=12, pady=12)
        window.bind("<Escape>", lambda _event: window.destroy())
        window.focus_set()

    def remove_image(self, index: int) -> None:
        if self.preview is not None and self.preview.winfo_exists():
            self.preview.destroy()
        del self.images[index]
        self.update_attachments()
        self.set_status("Image removed.")

    def clear_session(self) -> None:
        if self.cancel is not None:
            return
        if self.preview is not None and self.preview.winfo_exists():
            self.preview.destroy()
        self.images.clear()
        self.latest_capture = None
        self.capture_preview_button.configure(state="disabled")
        self.question.delete("1.0", "end")
        self.show_answer("")
        self.update_attachments()
        self.set_status("Session cleared.")

    def copy(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)

    def copy_answer(self) -> None:
        if self.answer:
            self.copy(self.answer)
            self.set_status("Answer copied.", SUCCESS)

    def show_answer(self, answer: str) -> None:
        self.answer = answer
        self.result.configure(state="normal", text_color=TEXT if answer else MUTED)
        self.result.delete("1.0", "end")
        self.result.insert("1.0", answer or "Your answer will appear here.")
        self.result.configure(state="disabled")
        self.result.see("1.0")
        self.copy_button.configure(state="normal" if answer else "disabled")

    def show_setup(self) -> None:
        if self.setup is not None and self.setup.winfo_exists():
            self.setup.lift()
            return
        window = ctk.CTkToplevel(self, fg_color=CARD)
        self.setup = window
        window.title("ChatGPT connection")
        window.transient(self)
        window.resizable(False, False)
        self.label(window, "ChatGPT connection", size=21, bold=True, text_color=TEXT).pack(
            anchor="w", padx=20, pady=(17, 3)
        )
        self.setup_status = self.label(
            window, text_color=MUTED, width=372, wraplength=372, justify="left", anchor="w"
        )
        self.setup_status.pack(anchor="w", padx=20)
        self.label(
            window, "Sign in from your terminal with codex login.", text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(6, 10))
        actions = ctk.CTkFrame(window, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 16))
        self.button(actions, "Install Codex", lambda: webbrowser.open(INSTALL_URL)).pack(
            side="left"
        )
        self.check_button = self.button(
            actions, "Check again", self.refresh_connection, width=98
        )
        self.check_button.pack(side="right")
        window.bind("<Escape>", lambda _event: window.destroy())
        self.update_connection_display()
        window.focus_set()

    def refresh_connection(self) -> None:
        if self.checking_connection or self.closing:
            return
        self.checking_connection = True
        self.update_connection_display()
        Thread(target=self.run_connection_check, daemon=True).start()

    def run_connection_check(self) -> None:
        try:
            connection = check_connection()
        except Exception:
            LOG.exception("Unexpected error checking Codex")
            connection = Connection(None, "Could not check Codex. Check your CLI installation.")
        self.events.put(("connection", connection))

    def update_connection_display(self) -> None:
        connected = self.connection.executable is not None
        text = "ChatGPT connected" if connected else "Set up ChatGPT"
        color = SUCCESS if connected else TEXT
        self.account_button.configure(
            text="Checking ChatGPT…" if self.checking_connection else text, text_color=color
        )
        if self.setup is not None and self.setup.winfo_exists():
            message = (
                "Checking for your ChatGPT login…" if self.checking_connection
                else self.connection.message
            )
            self.setup_status.configure(text=message)
            self.check_button.configure(state="disabled" if self.checking_connection else "normal")
        ready = "normal" if connected and not self.checking_connection else "disabled"
        busy = self.cancel is not None
        self.capture_button.configure(state="disabled" if busy else ready)
        self.area_button.configure(state="disabled" if busy else "normal")
        if not busy:
            self.ask_button.configure(state=ready)

    def ask_shortcut(self, _event: tk.Event) -> str:
        if self.cancel is None and self.ask_button.cget("state") == "normal":
            self.ask_or_stop()
        return "break"

    def ask_or_stop(self) -> None:
        if self.cancel is not None:
            self.cancel.set()
            self.ask_button.configure(text="Stopping…", state="disabled")
            self.set_status("Stopping the request…")
            return

        self.start_request(tuple(self.images))

    def start_request(
        self, images: tuple[Image.Image, ...], *, default_question: str = ""
    ) -> None:
        executable = self.connection.executable
        if not executable or self.checking_connection or self.closing or self.cancel is not None:
            return
        question = self.question.get("1.0", "end-1c").strip() or default_question
        if not question and not images:
            self.set_status("Enter a question or attach a screenshot.", ERROR)
            self.question.focus_set()
            return

        preset = self.model_menu.get()
        self.cancel = Event()
        self.ask_button.configure(text="Stop")
        self.clear_button.configure(state="disabled")
        self.model_menu.configure(state="disabled")
        self.update_connection_display()
        self.set_status(f"Asking {preset}…")
        Thread(
            target=self.run_request,
            args=(executable, preset, question, images, self.cancel),
        ).start()

    def run_request(
        self,
        executable: str,
        preset: str,
        question: str,
        images: tuple[Image.Image, ...],
        cancel: Event,
    ) -> None:
        try:
            self.events.put(("answer", ask_codex(executable, preset, question, images, cancel)))
        except RequestCancelled:
            self.events.put(("canceled", None))
        except CodexError as exc:
            self.events.put(("error", str(exc)))
        except Exception:
            LOG.exception("Unexpected error running Codex")
            self.events.put(("error", "Something went wrong with this request. Try again."))

    def poll_events(self) -> None:
        while True:
            try:
                event, value = self.events.get_nowait()
            except Empty:
                break
            if event == "connection":
                self.connection = value
                self.checking_connection = False
                self.update_connection_display()
                if self.status.cget("text") == "Checking ChatGPT connection…":
                    color = SUCCESS if value.executable else ERROR
                    self.set_status(value.message, color)
                continue

            canceled = self.cancel is not None and self.cancel.is_set()
            self.cancel = None
            if self.closing:
                self.destroy()
                return
            self.ask_button.configure(text="Ask ChatGPT")
            self.clear_button.configure(state="normal")
            self.model_menu.configure(state="normal")
            self.update_connection_display()
            if canceled or event == "canceled":
                self.set_status("Request stopped.")
            elif event == "answer":
                self.show_answer(value)
                self.set_status("Answer ready.", SUCCESS)
            else:
                self.set_status(value, ERROR)
        self.after(60, self.poll_events)

    def close(self) -> None:
        self.closing = True
        if self.cancel is None:
            self.destroy()
            return
        self.cancel.set()
        self.withdraw()


if __name__ == "__main__":
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        from ctypes import windll

        # Give the external Codex process Windows' standard DLL search path.
        if not windll.kernel32.SetDllDirectoryW(None):
            LOG.warning("Could not restore the default Windows DLL search path")
    ctk.set_appearance_mode("system")
    ScreenAssistant().mainloop()
