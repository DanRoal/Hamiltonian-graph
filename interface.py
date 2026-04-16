import customtkinter as ctk
import tkinter as tk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        self.title("HamGraph")
        self.geometry('480x600')
        self.minsize(400,600)
        self.columnconfigure((0,1,2,3), weight=1)
        #self.rowconfigure(0, weight=1)

        # Le pedimos al usuario la cantidad de átomos
        self.atomos = ctk.CTkEntry(self, placeholder_text= 'Átomos', fg_color= '#010101',width =220,height=40,
            justify= tk.CENTER)       
        self.atomos.grid(columnspan=2, row=0,padx=4, pady =4)

        self.tiempo = ctk.CTkEntry(self, placeholder_text= 'Tiempo', fg_color= '#010101',width =220,height=40,
            justify= tk.CENTER)       
        self.tiempo.grid(columnspan=2, row=1,padx=4, pady =4)

        self.pasos = ctk.CTkEntry(self, placeholder_text= 'Pasos', fg_color= '#010101',width =220,height=40,
            justify= tk.CENTER)       
        self.pasos.grid(columnspan=2, row=2,padx=4, pady =4)

        self.trabajadores = ctk.CTkEntry(self, placeholder_text= 'Trabajadores', fg_color= '#010101',width =220,height=40,
            justify= tk.CENTER)       
        self.trabajadores.grid(columnspan=2, row=3,padx=4, pady =4)




        self.radio_var = tk.IntVar(value=0)
        radiobutton_1 = ctk.CTkRadioButton(self, text="CTkRadioButton 1", command=self.radiobutton_event, variable= self.radio_var, value=1)
        radiobutton_2 = ctk.CTkRadioButton(self, text="CTkRadioButton 2", command=self.radiobutton_event, variable= self.radio_var, value=2)
        radiobutton_1.grid(row=10, column=0)
        radiobutton_2.grid(row=10, column=1)

    def radiobutton_event(self):
        print("radiobutton toggled, current value:", self.radio_var.get())
