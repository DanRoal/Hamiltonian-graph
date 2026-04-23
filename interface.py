import customtkinter as ctk
import tkinter as tk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        self.title("HamGraph")
        self.geometry('480x600')
        self.minsize(400,600)
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure((0,1), weight=1)

        ## Renderizamos los parámetros que necesitamos###
        self.parametros_frame = ParametrosFrame(self, parametros=["N_CAV", "N_ATOMOS","TIEMPO","PASOS","TRABAJADORES","EPSILON_IN","EPSILON_OUT","LAMDA_IN","LAMDA_OUT","DIVISIONES_EPSILON","DIVISIONES_LAMDA"])
        self.parametros_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsw")


        self.radio_var = tk.IntVar(value=0)
        radiobutton_1 = ctk.CTkRadioButton(self, text="CTkRadioButton 1", command=self.radiobutton_event, variable= self.radio_var, value=1)
        radiobutton_2 = ctk.CTkRadioButton(self, text="CTkRadioButton 2", command=self.radiobutton_event, variable= self.radio_var, value=2)
        radiobutton_1.grid(row=1, column=0)
        radiobutton_2.grid(row=1, column=1)

    def radiobutton_event(self):
        print("radiobutton toggled, current value:", self.radio_var.get())

class ParametrosFrame(ctk.CTkFrame):
    def __init__(self, master, parametros):
        super().__init__(master)
        self.parametros = parametros
        self.entradas = []

        for i, parametro in enumerate(self.parametros):
            entrada = ctk.CTkEntry(self, placeholder_text= f'{parametro}', fg_color= '#010101',width =220,height=40,justify= tk.CENTER)
            entrada.grid(row=i, column = 0, padx=10, pady=(10,0),sticky="w")
            self.entradas.append(entrada)
    
    def get(self):
        valores_parametros = {}
        for entrada in self.entradas:
            if entrada.get() != "":
                valores_parametros[entrada.cget("placeholder_text")] = entrada.get()
        return valores_parametros



