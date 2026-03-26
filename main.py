import webbrowser
import tkinter as tk
import platform

import customtkinter
import pyautogui
from PIL import Image, ImageTk

from functions import (
    get_available_models,
    get_image_count,
    get_selected_model,
    get_selected_region,
    initialize_client,
    restart_ss,
    send_to_api,
    set_selected_region,
    set_model,
    show_final,
    take_ss,
)


if platform.system() == "Windows":
    UI_FONT = "Segoe UI"
    UI_FONT_DISPLAY = "Segoe UI"
elif platform.system() == "Darwin":
    UI_FONT = "SF Pro Text"
    UI_FONT_DISPLAY = "SF Pro Display"
else:
    UI_FONT = "DejaVu Sans"
    UI_FONT_DISPLAY = "DejaVu Sans"


def set_status(message, color="gray75"):
    status_label.configure(text=message, text_color=color)


def update_image_count():
    image_count_label.configure(text=f"Screenshots: {get_image_count()}")


def update_region_label():
    region = get_selected_region()
    if region is None:
        region_label.configure(text="Capture area: Not set")
        return

    x_pos, y_pos, width, height = region
    region_label.configure(
        text=f"Capture area: x={x_pos}, y={y_pos}, w={width}, h={height}"
    )


def open_region_selector():
    screenshot_image = pyautogui.screenshot()

    app.attributes("-topmost", False)
    app.withdraw()
    app.update_idletasks()

    overlay = tk.Toplevel(app)
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)
    overlay.configure(bg="black")
    overlay.title("Select Capture Area")

    overlay.update_idletasks()
    screen_width = overlay.winfo_screenwidth()
    screen_height = overlay.winfo_screenheight()

    if screenshot_image.size != (screen_width, screen_height):
        screenshot_image = screenshot_image.resize(
            (screen_width, screen_height),
            Image.Resampling.LANCZOS,
        )

    canvas = tk.Canvas(overlay, cursor="cross", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    tk_screenshot = ImageTk.PhotoImage(screenshot_image)
    canvas.create_image(0, 0, image=tk_screenshot, anchor="nw")
    overlay._tk_screenshot = tk_screenshot

    instruction_id = canvas.create_text(
        20,
        20,
        anchor="nw",
        fill="#ffffff",
        font=("Helvetica", 16, "bold"),
        text="Drag to select area. Press Esc to cancel.",
    )
    instruction_bg = canvas.create_rectangle(
        canvas.bbox(instruction_id),
        fill="#000000",
        outline="#000000",
    )
    canvas.tag_lower(instruction_bg, instruction_id)

    start_x = 0
    start_y = 0
    rect_id = None
    selected = {"region": None}

    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x = event.x
        start_y = event.y
        if rect_id is not None:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            start_x,
            start_y,
            start_x,
            start_y,
            outline="#00e5ff",
            width=3,
        )

    def on_drag(event):
        nonlocal rect_id
        if rect_id is None:
            return
        canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_release(event):
        x0 = min(start_x, event.x)
        y0 = min(start_y, event.y)
        x1 = max(start_x, event.x)
        y1 = max(start_y, event.y)

        width = x1 - x0
        height = y1 - y0
        if width < 8 or height < 8:
            selected["region"] = None
        else:
            selected["region"] = (x0, y0, width, height)

        overlay.destroy()

    def cancel(_event=None):
        selected["region"] = None
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    overlay.bind("<Escape>", cancel)

    overlay.focus_force()
    app.wait_window(overlay)

    app.deiconify()
    app.attributes("-topmost", True)
    app.lift()
    app.focus_force()

    return selected["region"]


def set_capture_area():
    set_status("Drag to select area. Press Esc to cancel.", "#ffca3a")
    chosen_region = open_region_selector()
    if chosen_region is None:
        set_status("Area selection canceled. Using previous area.", "#ffca3a")
        return

    set_selected_region(chosen_region)
    update_region_label()
    set_status("Capture area updated.", "#8ac926")


def take_screenshot():
    try:
        if get_selected_region() is None:
            set_status("Select a capture area first.", "#ffca3a")
            chosen_region = open_region_selector()
            if chosen_region is None:
                set_status("Capture canceled. No area selected.", "#ff595e")
                return
            set_selected_region(chosen_region)
            update_region_label()

        take_ss()
        update_image_count()
        set_status("Screenshot captured from selected area.", "#8ac926")
    except Exception as exc:
        set_status(f"Could not capture screenshot: {exc}", "#ff595e")


def preview_screenshots():
    if get_image_count() == 0:
        set_status("Capture at least one screenshot first.", "#ffca3a")
        return

    try:
        show_final()
        set_status("Opened screenshot preview.", "#8ac926")
    except Exception as exc:
        set_status(f"Could not open preview: {exc}", "#ff595e")


def restart_screenshots():
    restart_ss(result_textbox)
    adjust_response_box_height()
    update_image_count()
    set_status("Session cleared.", "#1982c4")


def on_model_change(choice):
    set_model(choice)
    set_status(f"Model set to: {choice}", "#1982c4")


def set_api_key():
    success, message = initialize_client(api_key_entry.get())
    if success:
        api_key_entry.configure(state="disabled")
        set_key_button.configure(state="disabled")
        ask_button.configure(state="normal")
        set_status(message, "#8ac926")
    else:
        set_status(message, "#ff595e")


def ask_ai():
    ask_button.configure(state="disabled")
    set_status(f"Asking {get_selected_model()}...", "#ffca3a")
    app.update_idletasks()

    success = send_to_api(result_textbox)
    adjust_response_box_height()
    if success:
        set_status("Answer generated successfully.", "#8ac926")
    else:
        set_status("Could not generate answer. Check message below.", "#ff595e")

    if current_layout_mode == "compact":
        app.after(80, scroll_to_response_bottom)

    ask_button.configure(state="normal")


help_panel_visible = False


def open_link(url):
    try:
        webbrowser.open(url)
    except Exception as exc:
        set_status(f"Could not open link: {exc}", "#ff595e")


def toggle_help_panel():
    global help_panel_visible

    if help_panel_visible:
        help_content_frame.pack_forget()
        help_button.configure(text="Get API key (beginner guide)")
        help_panel_visible = False
        return

    help_content_frame.pack(padx=12, pady=(0, 12), fill="x")
    help_button.configure(text="Hide API/model guide")
    help_panel_visible = True


def scroll_help_guide(event):
    try:
        if hasattr(event, "num") and event.num == 4:
            step = -1
        elif hasattr(event, "num") and event.num == 5:
            step = 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return "break"
            step = -1 if delta > 0 else 1

        help_text._textbox.yview_scroll(step, "units")
    except Exception:
        pass
    return "break"


def adjust_response_box_height():
    app.update_idletasks()
    try:
        display_lines = int(result_textbox.count("1.0", "end-1c", "displaylines")[0])
    except Exception:
        text_value = result_textbox.get("1.0", "end-1c")
        display_lines = max(1, text_value.count("\n") + 1)

    target_height = max(180, display_lines * 24 + 20)
    result_textbox.configure(height=target_height)


def scroll_to_response_bottom():
    try:
        content_frame._parent_canvas.yview_moveto(1.0)
    except Exception:
        pass


customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")

app = customtkinter.CTk()
app.title("BadApp3 - OCR Assistant")
app.geometry("560x720")
app.minsize(560, 560)
app.resizable(True, True)
app.attributes("-topmost", True)

content_frame = customtkinter.CTkScrollableFrame(app)
content_frame.pack(fill="both", expand=True)

header = customtkinter.CTkFrame(content_frame)
header.pack(padx=20, pady=(18, 8), fill="x")

title_label = customtkinter.CTkLabel(
    header,
    text="BadApp3 OCR Assistant",
    font=(UI_FONT_DISPLAY, 26, "bold"),
)
title_label.pack(anchor="w", padx=14, pady=(12, 0))

subtitle_label = customtkinter.CTkLabel(
    header,
    text=(
        "Capture one or more screenshots, extract text with OCR, and ask the model for help."
    ),
    font=(UI_FONT, 14),
)
subtitle_label.pack(anchor="w", padx=14, pady=(2, 12))

config_frame = customtkinter.CTkFrame(content_frame)
config_frame.pack(padx=20, pady=8, fill="x")

model_label = customtkinter.CTkLabel(
    config_frame,
    text="Model",
    font=(UI_FONT, 14, "bold"),
)
model_label.grid(row=0, column=0, padx=(14, 8), pady=14, sticky="w")

model_menu = customtkinter.CTkOptionMenu(
    config_frame,
    values=get_available_models(),
    command=on_model_change,
    width=250,
)
model_menu.set(get_selected_model())
model_menu.grid(row=0, column=1, padx=(0, 16), pady=14, sticky="w")

key_label = customtkinter.CTkLabel(
    config_frame,
    text="GitHub API key",
    font=(UI_FONT, 14, "bold"),
)
key_label.grid(row=0, column=2, padx=(8, 8), pady=14, sticky="w")

api_key_entry = customtkinter.CTkEntry(config_frame, width=250, show="*")
api_key_entry.grid(row=0, column=3, padx=(0, 10), pady=14, sticky="ew")

set_key_button = customtkinter.CTkButton(
    config_frame,
    text="Connect",
    command=set_api_key,
    width=92,
)
set_key_button.grid(row=0, column=4, padx=(0, 14), pady=14)

config_frame.grid_columnconfigure(3, weight=1)

help_button_frame = customtkinter.CTkFrame(content_frame)
help_button_frame.pack(padx=20, pady=8, fill="x")

help_button = customtkinter.CTkButton(
    help_button_frame,
    text="Get API key (beginner guide)",
    command=toggle_help_panel,
    fg_color="#4361ee",
    hover_color="#3651c9",
    height=38,
)
help_button.pack(padx=12, pady=12, anchor="w")

help_content_frame = customtkinter.CTkFrame(help_button_frame)

help_title = customtkinter.CTkLabel(
    help_content_frame,
    text="GitHub API Key Setup (Step-by-Step for Beginners)",
    font=(UI_FONT, 16, "bold"),
)
help_title.pack(anchor="w", padx=14, pady=(12, 6))

help_subtitle = customtkinter.CTkLabel(
    help_content_frame,
    text="No coding experience needed. Follow these steps in order.",
    text_color="#c7d0dd",
    font=(UI_FONT, 13),
)
help_subtitle.pack(anchor="w", padx=14, pady=(0, 8))

help_text = customtkinter.CTkTextbox(help_content_frame, height=310, wrap="word")
help_text.pack(padx=14, pady=(0, 10), fill="x")
help_text.insert(
    "1.0",
    "Before you start:\n"
    "- You only need a GitHub account and this app open.\n"
    "- Keep this window open while you create the key in your browser.\n\n"
    "Step 1 - Sign in to GitHub\n"
    "- Open github.com and sign in.\n"
    "- If you do not have an account yet, create one first.\n\n"
    "Step 2 - Open token settings\n"
    "- Click your profile photo (top-right).\n"
    "- Click Settings > Developer settings > Personal access tokens.\n"
    "- You can use either:\n"
    "  * Fine-grained token (recommended for beginners)\n"
    "  * Tokens (classic)\n\n"
    "Step 3 - Create the token\n"
    "- Click Generate new token.\n"
    "- Give it a name like: BadApp3 Token.\n"
    "- Set an expiration date (for example, 30 days or 90 days).\n"
    "- Important: enable model access permission (`models:read`).\n\n"
    "Step 4 - Copy and save the token\n"
    "- Click Generate token at the bottom of the page.\n"
    "- Copy the token immediately and keep it safe.\n"
    "- GitHub may not show the full token again later.\n\n"
    "Step 5 - Connect in this app\n"
    "- Paste the token into the GitHub API key field above.\n"
    "- Click Connect.\n"
    "- Wait for a success status message.\n\n"
    "If something does not work:\n"
    "- Invalid key error: create a new token and ensure `models:read` is enabled.\n"
    "- Rate limited: switch model to `openai/gpt-4.1-mini` or `openai/gpt-4o-mini`.\n"
    "- Still stuck: open the docs button below and follow GitHub's screenshots.\n\n"
    "Plan notes:\n"
    "- GitHub Free works with GitHub Models (lower limits).\n"
    "- GitHub Pro / Pro Education usually gets higher limits on some tiers.\n",
)
help_text.configure(state="disabled")
help_text.bind("<MouseWheel>", scroll_help_guide)
help_text.bind("<Button-4>", scroll_help_guide)
help_text.bind("<Button-5>", scroll_help_guide)
help_text._textbox.bind("<MouseWheel>", scroll_help_guide)
help_text._textbox.bind("<Button-4>", scroll_help_guide)
help_text._textbox.bind("<Button-5>", scroll_help_guide)

links_row = customtkinter.CTkFrame(help_content_frame)
links_row.pack(padx=14, pady=(0, 12), fill="x")

token_link_button = customtkinter.CTkButton(
    links_row,
    text="Open Token Settings",
    command=lambda: open_link("https://github.com/settings/tokens"),
    fg_color="#3a86ff",
    hover_color="#2d6fd3",
)
token_link_button.grid(row=0, column=0, padx=(0, 10), pady=8, sticky="ew")

pat_docs_button = customtkinter.CTkButton(
    links_row,
    text="Open PAT Docs",
    command=lambda: open_link(
        "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
    ),
    fg_color="#577590",
    hover_color="#486177",
)
pat_docs_button.grid(row=0, column=1, pady=8, sticky="ew")

models_link_button = customtkinter.CTkButton(
    links_row,
    text="Open Models Marketplace",
    command=lambda: open_link("https://github.com/marketplace/models"),
    fg_color="#ff006e",
    hover_color="#d1005d",
)
models_link_button.grid(row=1, column=0, padx=(0, 10), pady=8, sticky="ew")

docs_link_button = customtkinter.CTkButton(
    links_row,
    text="Open GitHub Models Docs",
    command=lambda: open_link(
        "https://docs.github.com/en/github-models/prototyping-with-ai-models"
    ),
    fg_color="#2a9d8f",
    hover_color="#21867a",
)
docs_link_button.grid(row=1, column=1, pady=8, sticky="ew")

for column in range(2):
    links_row.grid_columnconfigure(column, weight=1)

meta_frame = customtkinter.CTkFrame(content_frame)
meta_frame.pack(padx=20, pady=8, fill="x")

status_label = customtkinter.CTkLabel(
    meta_frame,
    text="Add API key and capture screenshots to begin.",
    text_color="gray75",
    font=(UI_FONT, 14),
)
status_label.grid(row=0, column=0, padx=14, pady=12, sticky="w")

region_label = customtkinter.CTkLabel(
    meta_frame,
    text="Capture area: Not set",
    text_color="#adb5bd",
    font=(UI_FONT, 13),
)
region_label.grid(row=0, column=1, padx=10, pady=12, sticky="e")

image_count_label = customtkinter.CTkLabel(
    meta_frame,
    text="Screenshots: 0",
    text_color="#1982c4",
    font=(UI_FONT, 14, "bold"),
)
image_count_label.grid(row=0, column=2, padx=14, pady=12, sticky="e")

meta_frame.grid_columnconfigure(0, weight=1)

controls = customtkinter.CTkFrame(content_frame)
controls.pack(padx=20, pady=8, fill="x")

capture_button = customtkinter.CTkButton(
    controls,
    text="Capture Screenshot",
    command=take_screenshot,
    height=38,
)
capture_button.grid(row=0, column=0, padx=10, pady=12, sticky="ew")

set_area_button = customtkinter.CTkButton(
    controls,
    text="Set / Change Area",
    command=set_capture_area,
    fg_color="#4c6ef5",
    hover_color="#3b5bdb",
    height=38,
)
set_area_button.grid(row=0, column=1, padx=10, pady=12, sticky="ew")

preview_button = customtkinter.CTkButton(
    controls,
    text="Preview Captures",
    command=preview_screenshots,
    height=38,
)
preview_button.grid(row=0, column=2, padx=10, pady=12, sticky="ew")

clear_button = customtkinter.CTkButton(
    controls,
    text="Clear Session",
    command=restart_screenshots,
    fg_color="#6c757d",
    hover_color="#5b636a",
    height=38,
)
clear_button.grid(row=0, column=3, padx=10, pady=12, sticky="ew")

ask_button = customtkinter.CTkButton(
    controls,
    text="Ask AI",
    command=ask_ai,
    fg_color="#2a9d8f",
    hover_color="#21867a",
    height=38,
    state="disabled",
)
ask_button.grid(row=0, column=4, padx=10, pady=12, sticky="ew")

for column in range(5):
    controls.grid_columnconfigure(column, weight=1)

current_layout_mode = None


def apply_responsive_layout(window_width):
    global current_layout_mode

    new_mode = "compact" if window_width < 900 else "wide"
    if new_mode == current_layout_mode:
        return
    current_layout_mode = new_mode

    if new_mode == "compact":
        model_label.grid_configure(
            row=0, column=0, padx=(14, 8), pady=(12, 6), sticky="w"
        )
        model_menu.configure(width=170)
        model_menu.grid_configure(
            row=0,
            column=1,
            columnspan=2,
            padx=(0, 14),
            pady=(12, 6),
            sticky="ew",
        )
        key_label.grid_configure(
            row=1, column=0, padx=(14, 8), pady=(6, 12), sticky="w"
        )
        api_key_entry.grid_configure(
            row=1, column=1, padx=(0, 10), pady=(6, 12), sticky="ew"
        )
        set_key_button.grid_configure(
            row=1, column=2, padx=(0, 14), pady=(6, 12), sticky="ew"
        )

        config_frame.grid_columnconfigure(0, weight=0)
        config_frame.grid_columnconfigure(1, weight=1)
        config_frame.grid_columnconfigure(2, weight=0)
        config_frame.grid_columnconfigure(3, weight=0)
        config_frame.grid_columnconfigure(4, weight=0)

        status_label.grid_configure(
            row=0, column=0, columnspan=2, padx=14, pady=(10, 4), sticky="w"
        )
        region_label.grid_configure(row=1, column=0, padx=14, pady=(0, 10), sticky="w")
        image_count_label.grid_configure(
            row=1, column=1, padx=14, pady=(0, 10), sticky="e"
        )
        meta_frame.grid_columnconfigure(0, weight=1)
        meta_frame.grid_columnconfigure(1, weight=0)
        meta_frame.grid_columnconfigure(2, weight=0)

        capture_button.grid_configure(
            row=0, column=0, padx=10, pady=(12, 8), sticky="ew"
        )
        set_area_button.grid_configure(
            row=0, column=1, padx=10, pady=(12, 8), sticky="ew"
        )
        preview_button.grid_configure(row=1, column=0, padx=10, pady=8, sticky="ew")
        clear_button.grid_configure(row=1, column=1, padx=10, pady=8, sticky="ew")
        ask_button.grid_configure(
            row=2,
            column=0,
            columnspan=2,
            padx=10,
            pady=(8, 12),
            sticky="ew",
        )
        for column in range(5):
            controls.grid_columnconfigure(column, weight=0)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        token_link_button.grid_configure(
            row=0,
            column=0,
            columnspan=1,
            padx=(0, 10),
            pady=(8, 6),
            sticky="ew",
        )
        pat_docs_button.grid_configure(
            row=0,
            column=1,
            columnspan=1,
            padx=(0, 0),
            pady=(8, 6),
            sticky="ew",
        )
        models_link_button.grid_configure(
            row=1,
            column=0,
            columnspan=1,
            padx=(0, 10),
            pady=(6, 8),
            sticky="ew",
        )
        docs_link_button.grid_configure(
            row=1,
            column=1,
            columnspan=1,
            padx=(0, 0),
            pady=(6, 8),
            sticky="ew",
        )
        links_row.grid_columnconfigure(0, weight=1)
        links_row.grid_columnconfigure(1, weight=1)
        return

    model_label.grid_configure(row=0, column=0, padx=(14, 8), pady=14, sticky="w")
    model_menu.configure(width=250)
    model_menu.grid_configure(
        row=0, column=1, columnspan=1, padx=(0, 16), pady=14, sticky="w"
    )
    key_label.grid_configure(row=0, column=2, padx=(8, 8), pady=14, sticky="w")
    api_key_entry.grid_configure(row=0, column=3, padx=(0, 10), pady=14, sticky="ew")
    set_key_button.grid_configure(row=0, column=4, padx=(0, 14), pady=14, sticky="ew")

    config_frame.grid_columnconfigure(0, weight=0)
    config_frame.grid_columnconfigure(1, weight=0)
    config_frame.grid_columnconfigure(2, weight=0)
    config_frame.grid_columnconfigure(3, weight=1)
    config_frame.grid_columnconfigure(4, weight=0)

    status_label.grid_configure(
        row=0, column=0, columnspan=1, padx=14, pady=12, sticky="w"
    )
    region_label.grid_configure(row=0, column=1, padx=10, pady=12, sticky="e")
    image_count_label.grid_configure(row=0, column=2, padx=14, pady=12, sticky="e")
    meta_frame.grid_columnconfigure(0, weight=1)
    meta_frame.grid_columnconfigure(1, weight=0)
    meta_frame.grid_columnconfigure(2, weight=0)

    capture_button.grid_configure(
        row=0, column=0, columnspan=1, padx=10, pady=12, sticky="ew"
    )
    set_area_button.grid_configure(
        row=0, column=1, columnspan=1, padx=10, pady=12, sticky="ew"
    )
    preview_button.grid_configure(row=0, column=2, padx=10, pady=12, sticky="ew")
    clear_button.grid_configure(row=0, column=3, padx=10, pady=12, sticky="ew")
    ask_button.grid_configure(
        row=0, column=4, columnspan=1, padx=10, pady=12, sticky="ew"
    )
    for column in range(5):
        controls.grid_columnconfigure(column, weight=1)

    token_link_button.grid_configure(
        row=0, column=0, columnspan=1, padx=(0, 10), pady=8, sticky="ew"
    )
    pat_docs_button.grid_configure(
        row=0, column=1, columnspan=1, padx=(0, 0), pady=8, sticky="ew"
    )
    models_link_button.grid_configure(
        row=1, column=0, columnspan=1, padx=(0, 10), pady=8, sticky="ew"
    )
    docs_link_button.grid_configure(
        row=1, column=1, columnspan=1, padx=(0, 0), pady=8, sticky="ew"
    )
    links_row.grid_columnconfigure(0, weight=1)
    links_row.grid_columnconfigure(1, weight=1)


def on_window_resize(event):
    if event.widget is app:
        apply_responsive_layout(event.width)
        app.after_idle(adjust_response_box_height)


result_frame = customtkinter.CTkFrame(content_frame)
result_frame.pack(padx=20, pady=(8, 18), fill="both", expand=True)

result_title = customtkinter.CTkLabel(
    result_frame,
    text="AI Response",
    font=(UI_FONT, 16, "bold"),
)
result_title.pack(anchor="w", padx=14, pady=(12, 4))

result_textbox = customtkinter.CTkTextbox(result_frame, wrap="word")
result_textbox.pack(padx=14, pady=(0, 14), fill="both", expand=True)
result_textbox.insert("1.0", "AI response will appear here...")
result_textbox.configure(state="disabled")
result_textbox.bind("<MouseWheel>", lambda _event: "break")
result_textbox.bind("<Button-4>", lambda _event: "break")
result_textbox.bind("<Button-5>", lambda _event: "break")


def shortcut_capture(_event=None):
    take_screenshot()


def shortcut_ask(_event=None):
    if ask_button.cget("state") == "normal":
        ask_ai()


app.bind("<Control-Shift-S>", shortcut_capture)
app.bind("<Control-Return>", shortcut_ask)
app.bind("<Control-KP_Enter>", shortcut_ask)
app.bind("<Configure>", on_window_resize)

update_image_count()
update_region_label()
apply_responsive_layout(app.winfo_width())
adjust_response_box_height()
app.mainloop()
