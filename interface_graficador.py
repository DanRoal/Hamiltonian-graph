import customtkinter as ctk
from tkinter import filedialog
import pickle


class VentanaPrincipal(ctk.CTk):
    def __init__(self, fg_color = None, **kwargs):
        super().__init__(fg_color, **kwargs)
        ruta_file = filedialog.askopenfilename()
        if not ruta_file:
            return
        with open(ruta_file, "rb") as f:
            resultados = pickle.load(f)

        self.title("Visualizador de Resultados QuTiP")
        self.geometry("1300x900")
        self.minsize(1000, 700)
        self.columnconfigure(0, weight=1)
        self.rowconfigure((0,2), weight=0)
        self.rowconfigure(1, weight=1)

        ## Colocamos la sección de información ##
        info_frame = InfoFrame(self)
        info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ## Colocamos el fame con pestañas ##
        tabs_frame = PestañasFrame(self)
        tabs_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")




class SlidersFrame(ctk.CTkFrame):
    pass

class PestañasFrame(ctk.CTkTabview):
    pass

class InfoFrame(ctk.CTkFrame):
    pass