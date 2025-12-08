import pyautogui
import pyscreeze
from PIL import Image
import pytesseract
import os
from mistralai import Mistral, UserMessage, SystemMessage

# Global variables
final_input = []
final_string = ""
api_response = ""
client = None
endpoint = "https://models.github.ai/inference"
model = "mistral-ai/mistral-small-2503"


def get_image_count():
    #Get the number of screenshots
    return len(final_input)


def take_ss():
    #Take ss  and add it to final_input
    img1 = pyautogui.screenshot(region=(10, 40, 520, 860))
    final_input.append(img1)


def show_final():
    #show ss
    for img in final_input:
        img.show()


def restart_ss(result_textbox):
    #Clear all ss and text
    global final_string
    final_input.clear()
    final_string = ""
    result_textbox.configure(state="normal")
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", "API Response will appear here...")
    result_textbox.configure(state="disabled")


def imgToTxt():
    #extract text from ss
    global final_string
    final_string = ""  # Reset before extracting
    for i in final_input:
        final_string += pytesseract.image_to_string(i)
    print(final_string)


def initialize_client(api_key):
    #Initialize the API client with the provided key
    global client
    client = Mistral(api_key=api_key, server_url=endpoint)


def send_to_api(result_textbox):
    imgToTxt()
    #Send text to api and display response
    global final_string, api_response, client
    
    if client is None:
        result_textbox.configure(state="normal")
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", "Error: API key not set! Please enter your API key first.")
        result_textbox.configure(state="disabled")
        return
    
    if not final_string.strip():
        result_textbox.configure(state="normal")
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", "No text to send!")
        result_textbox.configure(state="disabled")
        return

    try:
        result_textbox.configure(state="normal")
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", "Loading...")
        result_textbox.configure(state="disabled")

        response = client.chat.complete(
            model=model,
            messages=[
                SystemMessage(content="You are a helpful assistant.Give me answer of this code follow all instructions. Use only c language. Give only c code no other text"),
                UserMessage(content=final_string),
            ],
            temperature=1.0,
            max_tokens=1000,
            top_p=1.0
        )
        api_response = response.choices[0].message.content
        result_textbox.configure(state="normal")
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", api_response)
        result_textbox.configure(state="disabled")
        print("API Response:")
        print(api_response)
    except Exception as e:
        result_textbox.configure(state="normal")
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", f"Error: {str(e)}")
        result_textbox.configure(state="disabled")
        print(f"API Error: {e}")