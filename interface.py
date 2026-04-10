import customtkinter as ctk

class Window:
    def __init__(self):
        pass




def hello():
    print("hello from button")

def basic_button(window, text, command = hello):
    button = ctk.CTkButton(window, text=text, command=command)
    button.grid(row = 0, column =0, padx = 20, pady=20)
