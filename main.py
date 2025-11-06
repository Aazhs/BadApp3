import customtkinter
from functions import take_ss, show_final, restart_ss, imgToTxt, send_to_api


app = customtkinter.CTk()       #app propertyies
app.geometry("500x600")
app.attributes("-topmost", True)

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