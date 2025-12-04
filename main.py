import customtkinter
from functions import take_ss, show_final, restart_ss, imgToTxt, send_to_api, initialize_client, get_image_count


def update_image_count():
    image_count_label.configure(text=f"No of images: {get_image_count()}")


def take_screenshot():
    take_ss()
    update_image_count()


def restart_screenshots():
    restart_ss(result_textbox)
    update_image_count()


def set_api_key():
    api_key = api_key_entry.get()
    if api_key.strip():
        initialize_client(api_key)
        status_label.configure(text="✓ API Key Set", text_color="green")
        api_key_entry.configure(state="disabled")
        set_key_button.configure(state="disabled")
    else:
        status_label.configure(text="⚠ Please enter a valid API key", text_color="red")


app = customtkinter.CTk()       #app propertyies
app.geometry("540x700")
app.attributes("-topmost", True)

# API Key section
api_key_frame = customtkinter.CTkFrame(app)
api_key_frame.pack(padx=20, pady=10, fill="x")

api_key_label = customtkinter.CTkLabel(api_key_frame, text="Mistral AI GitHub API Key:")
api_key_label.pack(side="left", padx=5)

api_key_entry = customtkinter.CTkEntry(api_key_frame, width=250, show="*")
api_key_entry.pack(side="left", padx=5)

set_key_button = customtkinter.CTkButton(api_key_frame, text="Set Key", command=set_api_key, width=80)
set_key_button.pack(side="left", padx=5)

# Status labels side by side
status_frame = customtkinter.CTkFrame(app)
status_frame.pack(padx=20, pady=10, fill="x")

status_label = customtkinter.CTkLabel(status_frame, text="⚠ API Key not set", text_color="orange")
status_label.pack(side="left", padx=20)

image_count_label = customtkinter.CTkLabel(status_frame, text="No of images: 0", text_color="blue", font=("Arial", 14, "bold"))
image_count_label.pack(side="left", padx=20)

# Buttons in 2x2 grid
button_frame = customtkinter.CTkFrame(app)
button_frame.pack(padx=20, pady=10)

# Row 1
button = customtkinter.CTkButton(button_frame, text="take screen shot", command=take_screenshot, width=230)
button.grid(row=0, column=0, padx=10, pady=10)

button2 = customtkinter.CTkButton(button_frame, text="show final image", command=show_final, width=230)
button2.grid(row=0, column=1, padx=10, pady=10)

# Row 2
button3 = customtkinter.CTkButton(button_frame, text="restart", command=restart_screenshots, width=230)
button3.grid(row=1, column=0, padx=10, pady=10)

button5 = customtkinter.CTkButton(button_frame, text="get answer", command=lambda: send_to_api(result_textbox), fg_color="green", width=230)
button5.grid(row=1, column=1, padx=10, pady=10)

result_textbox = customtkinter.CTkTextbox(app, width=450, height=300)
result_textbox.pack(padx=20, pady=20, fill="both", expand=True)
result_textbox.insert("1.0", "API Response will appear here...")
result_textbox.configure(state="disabled")

app.mainloop()