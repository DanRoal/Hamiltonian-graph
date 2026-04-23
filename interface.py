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

        ## Renderizamos los parámetros que necesitamos ##
        self.parametros_frame = ParametrosFrame(self, parametros=["N_CAV", "N_ATOMOS","TIEMPO","PASOS","TRABAJADORES","EPSILON_IN","EPSILON_OUT","LAMDA_IN","LAMDA_OUT","DIVISIONES_EPSILON","DIVISIONES_LAMDA"])
        self.parametros_frame.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="ew",columnspan=2)


        ## Renderizamos las opciones predeterminadas: ##
        self.hamiltonianos = ["Tavis-Cummings", "Dicke"]
        self.opciones_predeterminadas_frame = HamiltonianosPredeterminadosFrame(self, title="Opciones", values=self.hamiltonianos)
        self.opciones_predeterminadas_frame.grid(row=1, column = 0, padx=10, pady=(0,2), sticky="ew", columnspan=2)


        ## Le pasamos los valores a quitip y generamos el archivo.pkl ##
        

    def do_math():
        pass

    def render_graph_from_file():
        pass


class ParametrosFrame(ctk.CTkFrame):
    def __init__(self, master, parametros):
        super().__init__(master)
        self.parametros = parametros
        self.entradas = []
        self.columnconfigure(0, weight=1)

        for i, parametro in enumerate(self.parametros):
            entrada = ctk.CTkEntry(self, placeholder_text= f'{parametro}', fg_color= '#010101',justify= tk.CENTER)
            entrada.grid(row=i, column = 0, padx=10, pady=(5,5),sticky="n")
            self.entradas.append(entrada)
    
    def get(self):
        valores_parametros = {}
        for entrada in self.entradas:
            if entrada.get() != "":
                valores_parametros[entrada.cget("placeholder_text")] = entrada.get()
        return valores_parametros

class HamiltonianosPredeterminadosFrame(ctk.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.title = title
        self.values = values
        self.radio_var = tk.StringVar(value=None)
        self.options = []
        self.columnconfigure(0, weight=1)


        self.title = ctk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(5,5), sticky="ew")

        for i, value in enumerate(self.values):
            option = ctk.CTkRadioButton(self, text=f"{value}", command=self.radiobutton_event, variable= self.radio_var, value=value)
            option.grid(row=i+1, column = 0, padx=10, pady=(5,5),sticky="wn")

    def radiobutton_event(self):
        print("radiobutton toggled, current value:", self.radio_var.get())


