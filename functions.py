import pyautogui
import pyscreeze
from PIL import Image
import pytesseract
import os
from mistralai import Mistral, UserMessage, SystemMessage

# Initialize API client
token = os.environ.get("gtoken")
if not token:
    raise ValueError("gtoken environment variable not set")
endpoint = "https://models.github.ai/inference"
model = "mistral-ai/mistral-small-2503"
client = Mistral(api_key=token, server_url=endpoint)

# Global variables
final_input = []
final_string = ""
api_response = ""


def take_ss():
    #Take ss  and add it to final_input
    img1 = pyautogui.screenshot(region=(10, 180, 700, 680))
    final_input.append(img1)


def show_final():
    #show ss
    for img in final_input:
        img.show()


def restart_ss():
    #Clear all ss
    final_input.clear()


def imgToTxt():
    #extract text from ss
    global final_string
    for i in final_input:
        final_string += pytesseract.image_to_string(i)
        print(final_string)


def send_to_api(result_textbox):
    #Send text to api and display response
    global final_string, api_response
    if not final_string.strip():
        result_textbox.configure(state="normal")
        result_textbox.insert("1.0", "No text to send!")
        result_textbox.configure(state="disabled")
        return

    try:
        result_textbox.configure(state="normal")
        result_textbox.insert("1.0", "Loading...")
        result_textbox.configure(state="disabled")

        response = client.chat.complete(
            model=model,
            messages=[
                SystemMessage(content="You are a helpful assistant.give only the code no explaination.Give very simple standard code"),
                UserMessage(content=final_string),
            ],
            temperature=1.0,
            max_tokens=1000,
            top_p=1.0
        )
        api_response = response.choices[0].message.content
        result_textbox.configure(state="normal")
        result_textbox.insert("1.0", api_response)
        result_textbox.configure(state="disabled")
        print("API Response:")
        print(api_response)
    except Exception as e:
        result_textbox.configure(state="normal")
        result_textbox.insert("1.0", f"Error: {str(e)}")
        result_textbox.configure(state="disabled")
        print(f"API Error: {e}")