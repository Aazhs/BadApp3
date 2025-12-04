import customtkinter
from functions import take_ss, show_final, restart_ss, imgToTxt, send_to_api, initialize_client


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
app.geometry("500x700")
app.attributes("-topmost", True)

# API Key section
api_key_frame = customtkinter.CTkFrame(app)
api_key_frame.pack(padx=20, pady=10, fill="x")

api_key_label = customtkinter.CTkLabel(api_key_frame, text="GitHub API Key:")
api_key_label.pack(side="left", padx=5)

api_key_entry = customtkinter.CTkEntry(api_key_frame, width=250, show="*")
api_key_entry.pack(side="left", padx=5)

set_key_button = customtkinter.CTkButton(api_key_frame, text="Set Key", command=set_api_key, width=80)
set_key_button.pack(side="left", padx=5)

status_label = customtkinter.CTkLabel(app, text="⚠ API Key not set", text_color="orange")
status_label.pack(padx=20, pady=5)

# Existing buttons
button = customtkinter.CTkButton(app, text="take ss", command=take_ss)
button.pack(padx=20, pady=10)
button2 = customtkinter.CTkButton(app, text="show final", command=show_final)
button2.pack(padx=20, pady=10)
button3 = customtkinter.CTkButton(app, text="restart", command=lambda: restart_ss(result_textbox))
button3.pack(padx=20, pady=10)

button5 = customtkinter.CTkButton(app, text="Send to API", command=lambda: send_to_api(result_textbox), fg_color="green")
button5.pack(padx=20, pady=10)

result_textbox = customtkinter.CTkTextbox(app, width=450, height=300)
result_textbox.pack(padx=20, pady=20, fill="both", expand=True)
result_textbox.insert("1.0", "API Response will appear here...")
result_textbox.configure(state="disabled")

app.mainloop()