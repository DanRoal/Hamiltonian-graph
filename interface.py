import customtkinter as ctk
import tkinter as tk
import parametros_default
import matemáticas
import graficador

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        self.title("HamGraph")
        self.geometry('480x800')
        self.minsize(400,700)
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure((0,1), weight=1)

        ## Renderizamos los parámetros que necesitamos ##
        self.parametros_frame = ParametrosFrame(self)
        self.parametros_frame.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="new",columnspan=2)


        ## Renderizamos las opciones de hamiltonianos predeterminadas: ##
        self.hamiltonianos = {"Tavis-Cummings": "Tavis-Cummings",
                               "Dicke": "Dicke"}
        self.hamiltonianos_frame = OpcionesPredeterminadasFrame(self, title="Hamiltonianos", values=self.hamiltonianos)
        self.hamiltonianos_frame.grid(row=1, column = 0, padx=10, pady=(0,2), sticky="news", columnspan=1)

        ## Renderizamos las opciones de estados iniciales ##
        self.estados_iniciales = {"|ψ_0⟩ = |0⟩⊗|j,+j⟩": "+j",
                                "|ψ_0⟩ = |\\alpha⟩⊗|j,-j⟩": "alpha",
                                "|ψ_0⟩ = |up⟩⊗|j,-j⟩":"-j",
                                "|ψ_0⟩ = |up⟩⊗|j,-j⟩":"-j",
                                "|ψ_0⟩=|0⟩⊗(1/2^(1/2))(|j,j⟩+|j,j-1⟩)": "superpuesto",
                                "alph + beta": "coherente superpuesto"}
        self.estados_iniciales_frame = OpcionesPredeterminadasFrame(self, title="Estado inicial", values= self.estados_iniciales)
        self.estados_iniciales_frame.grid(row=1, column=1,pady=(0,2), sticky="news", columnspan=1)


        ## Hacemos el botón que le pasa los valores a quitip y generamos el archivo.pkl ##
        self.boton_quitip = ctk.CTkButton(self,text="Calcular", command=self.do_math)
        self.boton_quitip.grid(row=2,column = 0, padx=10, pady=(5, 5), sticky="ew",columnspan=2)
        self.boton_quitip = ctk.CTkButton(self,text="Graficar desde archivo", command=self.render_graph_from_file)
        self.boton_quitip.grid(row=3,column = 0, padx=10, pady=(5, 5), sticky="ew",columnspan=2)

    def do_math(self):
        matemáticas.master(HAMILTONIANO=self.hamiltonianos_frame.radio_var.get(), inicial=self.estados_iniciales_frame.radio_var.get(), **self.parametros_frame.get())

    def render_graph_from_file(self):
        graficador.graph(parent=self)


class ParametrosFrame(ctk.CTkFrame):
    def __init__(self, master, modulo_parametros = parametros_default):
        super().__init__(master)
        self.entradas = {}
        self.columnconfigure(0, weight=1)
        self.valores_default = {}

        ## Obtenemos el diccionario con los nombres de los parámetros ##
        nombres = getattr(modulo_parametros, "nombres",{})

        for key in nombres:
            self.valores_default[key] = getattr(modulo_parametros, key, None)

        for i, (parametro, etiqueta) in enumerate(nombres.items()):

            label = ctk.CTkLabel(self, text=etiqueta)
            label.grid(row=i, column= 0,padx=10, pady=(5,5),sticky="w")

            entrada = ctk.CTkEntry(self, placeholder_text=f"{self.valores_default[parametro]}", fg_color= '#010101',justify= tk.CENTER)
            entrada.grid(row=i, column = 1, padx=10, pady=(5,5),sticky="ew")

            self.entradas[parametro] = entrada
    
    def get(self):
        valores = {}
        for parametro, entrada in self.entradas.items():
            if entrada.get() == "":
                valores[parametro] = self.valores_default[parametro]
            else:
                valores[parametro] = int(entrada.get())
        return valores

class OpcionesPredeterminadasFrame(ctk.CTkFrame):
    def __init__(self, master, title:str, values:dict):
        super().__init__(master)
        self.title = title
        self.radio_var = tk.StringVar(value=list(values.values())[0])
        self.options = []
        self.columnconfigure(0, weight=1)


        self.title = ctk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(5,5), sticky="ew")

        for i, key in enumerate(values):
            option = ctk.CTkRadioButton(self, text=f"{key}", command=self.radiobutton_event, variable= self.radio_var, value=values[key])
            option.grid(row=i+1, column = 0, padx=10, pady=(5,5),sticky="wn")

    def radiobutton_event(self):
        print("radiobutton toggled, current value:", self.radio_var.get())


