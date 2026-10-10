import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import parametros_default
import matemáticas
from graficador import GraphApp
import pickle


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        self.title("HamGraph")
        self.minsize(800,700)
        self.columnconfigure((0,1,2), weight=1)
        self.after(100, lambda: self.state("zoomed"))
        self.rowconfigure(0, weight=1)

        self.parametros = {}
        self.resultados = {}


        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", columnspan = 2)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.frames["GraficadorFrame"] = GraficadorFrame(master=self.container, controller=self)
        self.frames["GraphApp"] = None
        self._managed_frames = {}

        self.show_screen("GraficadorFrame")

        self.valores = ValoresFrame(master=self)
        self.valores.grid(row=0, column = 0, padx = 5, pady=0, sticky = "nsew")

        

    def graph(self, path= None):
        file_path = path
        if not path:
            file_path = filedialog.askopenfilename()
        if not file_path:
            return
        with open(file_path, 'rb') as f:
            datos = pickle.load(f)

        self.parametros = datos["parametros"]
        self.resultados = datos
        self.resultados.pop("parametros", None)

        if "VISIBLE_EXPECTED" in self.parametros or "VISIBLE_METRICS" in self.parametros:
            self._updating_visibility_controls = True
            try:
                self.valores.expected_operators.set_selected(
                    self.parametros.get("VISIBLE_EXPECTED", [])
                )
                self.valores.metricas_extra.set_selected(
                    self.parametros.get("VISIBLE_METRICS", [])
                )
            finally:
                self._updating_visibility_controls = False
        else:
            self._update_graph_visibility()

        if self.frames["GraphApp"] is not None:
            self.frames["GraphApp"].destroy()
            self.frames["GraphApp"] = None
            self._managed_frames["GraphApp"] = False
        
        self.show_screen("GraphApp")

    def _update_graph_visibility(self):
        if getattr(self, "_updating_visibility_controls", False):
            return

        visible_expected = self.valores.expected_operators.get()
        visible_metrics = self.valores.metricas_extra.get()
        self.parametros["VISIBLE_EXPECTED"] = visible_expected
        self.parametros["VISIBLE_METRICS"] = visible_metrics

        graph_app = self.frames.get("GraphApp")
        if graph_app is not None:
            graph_app.update_visibility(visible_expected, visible_metrics)


    def do_math(self, ham, iniciales, parametros, operadores_visibles=None, metricas_visibles=None):

        operadores_visibles = operadores_visibles or []
        metricas_visibles = metricas_visibles or []
        if not operadores_visibles and not metricas_visibles:
            print("Selecciona al menos un operador o métrica para graficar")
            return

        nombre_archivo = filedialog.asksaveasfilename()
        if nombre_archivo == "":
            print("Nombre de archivo no válido")
            return

        parametros = dict(parametros)
        parametros["VISIBLE_EXPECTED"] = operadores_visibles
        parametros["VISIBLE_METRICS"] = metricas_visibles

        matemáticas.master(nombre_archivo, HAMILTONIANO= ham, 
                           inicial=iniciales, 
                           **parametros)
        nombre_archivo += ".pkl"
        self.graph(nombre_archivo)



    def show_screen(self, name) -> None:
        if isinstance(name, type):
            name = name.__name__

        if name == "GraphApp" and self.frames["GraphApp"] is None:
            self.frames["GraphApp"] = GraphApp(master=self.container, controller=self)

        frame = self.frames[name]
        if not self._managed_frames.get(name, False):
            frame.grid(row=0, column=0, sticky="nsew")
            self._managed_frames[name] = True

        frame.tkraise()

        
class GraficadorFrame(ctk.CTkFrame):
    def __init__(self, master, controller: "App"):
        super().__init__(master)

        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0,weight=1)

        self.button = ctk.CTkButton(self, text="Seleccionar archivo", command=controller.graph)
        self.button.grid(row = 0, column = 0, padx =10, pady = 10)


class ValoresFrame(ctk.CTkScrollableFrame):
    def __init__(self, master:"App"):
        super().__init__(master)

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
                                "|ψ_0⟩=|0⟩⊗(1/2^(1/2))(|j,j⟩+|j,j-1⟩)": "superpuesto",
                                "alph + beta": "coherente superpuesto"}
        self.estados_iniciales_frame = OpcionesPredeterminadasFrame(self, title="Estado inicial", values= self.estados_iniciales)
        self.estados_iniciales_frame.grid(row=1, column=1, pady=(0,2), sticky="news", columnspan=1)

        esperados={
            "names": [
                "⟨n⟩ (Número de fotones)",
                "⟨J_z⟩ (Inversión atómica)",
                "M = ⟨a^\\dagger a + J_z⟩",
                "⟨n^2⟩",
                "⟨J_x⟩",
                "⟨(J_x)^2⟩",
                "⟨q⟩",
                "⟨q^2⟩",
                "⟨p⟩",
                "⟨p^2⟩",
            ],
        }

        damping = [
            "a",
            "a\\dagger",
            "J-",
            "J+",
        ]

        self.expected_operators = OperadoresFrame(
            self,
            title="Operadores esperados",
            values=esperados["names"],
            on_change=master._update_graph_visibility,
        )
        self.expected_operators.grid(row=2, column = 0, pady=2, sticky ="news")

        self.metricas_extra = OperadoresFrame(
            self,
            title="Gráficas extra",
            values=[
                "Parámetro Mandel",
                "Parámetro Compresión Spin",
                "Δq",
                "Δp",
                "ξ²_q",
                "ξ²_p",
                "Entropía de Von Neumann",
                "Pureza",
            ],
            on_change=master._update_graph_visibility,
        )
        self.metricas_extra.grid(row=2, column=1, pady=2, sticky="news")

        self.damping_operators = OperadoresFrame(self, title="Damping operators", values= damping)
        self.damping_operators.grid(row = 3, column = 0, pady=2, sticky = "news")

        ## Hacemos el botón que le pasa los valores a quitip y generamos el archivo.pkl ##
        self.boton_quitip = ctk.CTkButton(
            self,
            text="Calcular",
            command=lambda: master.do_math(
                self.hamiltonianos_frame.radio_var.get(),
                self.estados_iniciales_frame.radio_var.get(),
                self.parametros_frame.get(),
                self.expected_operators.get(),
                self.metricas_extra.get(),
            )
        )
        self.boton_quitip.grid(row=4,column = 0, padx=10, pady=(5, 5), sticky="ew",columnspan=2)

        self.button_select = ctk.CTkButton(self, text="Selecionar archivo",command=master.graph)
        self.button_select.grid(row=5, column = 0, padx=10, pady=(5,5), sticky="ew", columnspan = 2)


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

            entrada = ctk.CTkEntry(self, placeholder_text=f"{self.valores_default[parametro]}", 
                                   fg_color= '#010101',
                                   justify= tk.CENTER)
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
            option = ctk.CTkRadioButton(self, text=f"{key}", variable= self.radio_var, value=values[key])
            option.grid(row=i+1, column = 0, padx=10, pady=(5,5),sticky="wn")

class OperadoresFrame(ctk.CTkFrame):
    def __init__(self, master, title:str, values:list, on_change=None):
        super().__init__(master)

        self.checkboxes = []
        self.on_change = on_change
        self.columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(5,5), sticky="ew")

        for i, key in enumerate(values):
            option = ctk.CTkCheckBox(self, text=key, command=self._notify_change)
            option.grid(row=i+1, column = 0, padx=10, pady=(5,5),sticky="w")
            if title == "Operadores esperados":
                option.select()
            self.checkboxes.append(option)

    def _notify_change(self):
        if self.on_change is not None:
            self.on_change()

    def set_selected(self, selected_values):
        selected_values = set(selected_values)
        for checkbox in self.checkboxes:
            if checkbox.cget("text") in selected_values:
                checkbox.select()
            else:
                checkbox.deselect()

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes


if __name__ == "__main__":
    root = App()
    root.mainloop()
