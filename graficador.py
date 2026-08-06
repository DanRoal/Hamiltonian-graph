import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkinter import filedialog
import customtkinter as ctk
from interface_graficador import VentanaPrincipal


def calcular_mandel(resultado: dict):
    for pareja in resultado:
        n = resultado[pareja]["expect_values"][0]
        n2 = resultado[pareja]["expect_values"][3]
        param_mandel = (n2 - n**2 - n) / n
        param_mandel = np.nan_to_num(param_mandel, nan=0.0)
        resultado[pareja]["expect_values"] = np.vstack([resultado[pareja]["expect_values"], param_mandel])


def calcular_compresion(resultado: dict, j: float):
    for pareja in resultado:
        Jx = resultado[pareja]["expect_values"][4]
        Jx2 = resultado[pareja]["expect_values"][5]
        Jz = resultado[pareja]["expect_values"][1]

        delta_jx_squared = Jx2 - Jx**2
        delta_jx = np.sqrt(delta_jx_squared)

        epsilon = 1e-10
        jz_abs = np.absolute(Jz)
        jz_abs = np.where(jz_abs < epsilon, epsilon, jz_abs)

        param_compresion = np.sqrt(2 * j) * delta_jx / jz_abs
        resultado[pareja]["expect_values"] = np.vstack([resultado[pareja]["expect_values"], param_compresion])


class InfoPanel(ctk.CTkFrame):
    def __init__(self, master, params: dict, **grid_kwargs):
        super().__init__(master, fg_color="gray25", corner_radius=8)
        self.params = params
        self.columnconfigure(0, weight=1)
        self._build()
        self.grid(**grid_kwargs)

    def _build(self):
        info_text = (f"N_cavidad: {self.params['N_CAV']}  |  N_átomos: {self.params['N_ATOMOS']}  |  "
                     f"Hamiltoniano: {self.params.get('HAMILTONIANO', 'Desconocido')}")
        ctk.CTkLabel(self, text=info_text, font=("Arial", 14, "bold")).pack(pady=(8, 4))

        damping_text = f"Damping operators: {', '.join(self.params.get('DAMPING_OPERATORS', ['Ninguno']))}"
        ctk.CTkLabel(self, text=damping_text, font=("Arial", 13), text_color="gray").pack(pady=(0, 4))

        initial_text = f"Estado inicial: {self.params.get('INITIAL', 'Desconocido')}"
        ctk.CTkLabel(self, text=initial_text, font=("Arial", 13), text_color="gray").pack(pady=(0, 8))


class PlotsPanel(ctk.CTkFrame):
    def __init__(self, master, resultados: dict, operator_names: list, times: np.ndarray, **grid_kwargs):
        super().__init__(master)
        self.resultados = resultados
        self.operator_names = operator_names
        self.times = times
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.lines = {}
        self.axes = {}
        self.canvases = {}
        self._build()
        self.grid(**grid_kwargs)

    def _build(self):
        self.tabview = ctk.CTkTabview(self, fg_color="gray20", segmented_button_fg_color="gray30",
                                      text_color="white", segmented_button_selected_color="#0d7377",
                                      segmented_button_selected_hover_color="#14919b")
        self.tabview.grid(row=0, column=0, sticky="nsew")

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

        # choose an arbitrary starting key (closest to some default)
        eps_init, g_init = 1.0, 0.25
        self.closest_init = min(self.resultados.keys(), key=lambda x: (x[0]-eps_init)**2 + (x[1]-g_init)**2)

        # create per-operator tabs and initial lines
        operator_ranges = self._compute_operator_ranges()
        for op_idx, name in enumerate(self.operator_names):
            tab = self.tabview.add(name)
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)

            fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
            ax.set_facecolor('white')
            self.axes[op_idx] = ax

            data = self.resultados[self.closest_init]
            y_data = data['expect_values'][op_idx]
            
            # Limitar compresión a máximo de 10 en visualización
            is_compresion = 'compresión' in name.lower()
            if is_compresion:
                y_data = np.clip(y_data, None, 10)
            
            line, = ax.plot(self.times, y_data, color=colors[op_idx % len(colors)], linewidth=2.5, antialiased=True)
            self.lines[op_idx] = line

            ax.set_xlabel("Tiempo (unidades arbitrarias)", fontsize=15, color='black', fontweight='bold')
            ax.set_ylabel(name, fontsize=15, color='black', fontweight='bold')
            ax.set_ylim(operator_ranges[op_idx])
            ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.7)
            ax.tick_params(colors='black', labelsize=12)
            ax.ticklabel_format(style='plain', useOffset=False)
            ax.yaxis.offsetText.set_visible(False)

            for spine in ax.spines.values():
                spine.set_edgecolor('#cccccc')
                spine.set_linewidth(1.2)

            ax.set_title(f"{name} | ε={self.closest_init[0]:.3f}, g={self.closest_init[1]:.3f}", color='black', fontsize=15, fontweight='bold', pad=15)

            self._setup_hover_cursor(fig, ax, line)

            canvas = FigureCanvasTkAgg(fig, master=tab)
            self.canvases[op_idx] = canvas
            canvas.draw()
            fig.tight_layout()
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # comparative tab: only add if both indices found
        fotones_idx = next((i for i, n in enumerate(self.operator_names) if 'fotones' in n.lower()), None)
        inv_idx = next((i for i, n in enumerate(self.operator_names) if 'inversión' in n.lower() or 'inversion' in n.lower()), None)
        # store indices for later safe updates
        self.fotones_idx = fotones_idx
        self.inv_idx = inv_idx
        if fotones_idx is not None and inv_idx is not None:
            tab_comp = self.tabview.add("Comparativa")
            # ensure the tab expands to fill available space
            tab_comp.columnconfigure(0, weight=1)
            tab_comp.rowconfigure(0, weight=1)
            fig_c, ax1 = plt.subplots(figsize=(12, 6), facecolor='white')
            ax1.set_facecolor('white')
            data_c = self.resultados[self.closest_init]
            line_f, = ax1.plot(self.times, data_c['expect_values'][fotones_idx], color='#1f77b4', linewidth=2.5, antialiased=True, label='Fotones')
            ax1.set_xlabel("Tiempo (unidades arbitrarias)", fontsize=15, color='black', fontweight='bold')
            ax1.set_ylabel("⟨n⟩ (Número de fotones)", fontsize=15, color='#1f77b4', fontweight='bold')
            ax1.tick_params(axis='y', labelcolor='#1f77b4', labelsize=12)
            ax1.ticklabel_format(style='plain', useOffset=False)
            ax1.yaxis.offsetText.set_visible(False)

            self._setup_hover_cursor(fig_c, ax1, line_f)

            ax2 = ax1.twinx()
            line_i, = ax2.plot(self.times, data_c['expect_values'][inv_idx], color='#d62728', linewidth=2.5, antialiased=True, linestyle='--', label='Inversión')
            ax2.set_ylabel("⟨J_z⟩ (Inversión atómica)", fontsize=15, color='#d62728', fontweight='bold')
            ax2.tick_params(axis='y', labelcolor='#d62728', labelsize=12)
            ax2.ticklabel_format(style='plain', useOffset=False)
            ax2.yaxis.offsetText.set_visible(False)
            self._setup_hover_cursor(fig_c, ax2, line_i)

            ax1.set_title(f"Intercambio de energía | ε={self.closest_init[0]:.3f}, g={self.closest_init[1]:.3f}", color='black', fontsize=15, fontweight='bold', pad=15)

            fotones_values = [d['expect_values'][fotones_idx] for d in self.resultados.values()]
            inversion_values = [d['expect_values'][inv_idx] for d in self.resultados.values()]
            fmin, fmax = min(np.min(a) for a in fotones_values), max(np.max(a) for a in fotones_values)
            imin, imax = min(np.min(a) for a in inversion_values), max(np.max(a) for a in inversion_values)
            mf = 0.1 * (fmax - fmin) if (fmax - fmin) != 0 else 0.5
            mi = 0.1 * (imax - imin) if (imax - imin) != 0 else 0.5
            ax1.set_ylim(fmin - mf, fmax + mf)
            ax2.set_ylim(imin - mi, imax + mi)

            canvas_c = FigureCanvasTkAgg(fig_c, master=tab_comp)
            canvas_c.draw()
            fig_c.tight_layout()
            canvas_c.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

            self.canvases['comparativa'] = canvas_c
            self.axes['comparativa_1'] = ax1
            self.axes['comparativa_2'] = ax2
            self.lines['comparativa_fotones'] = line_f
            self.lines['comparativa_inversion'] = line_i

    def _compute_operator_ranges(self):
        operator_ranges = {}
        for op_idx in range(len(self.operator_names)):
            op_values = []
            for data in self.resultados.values():
                op_values.extend(data['expect_values'][op_idx])

            if op_values:
                min_val = min(op_values)
                max_val = max(op_values)
                
                # Limitar compresión a máximo de 10 en visualización
                is_compresion = 'compresión' in self.operator_names[op_idx].lower()
                if is_compresion:
                    max_val = min(max_val, 10)
                
                margen = 0.1 * (max_val - min_val) if (max_val - min_val) != 0 else 0.5
                operator_ranges[op_idx] = (min_val - margen, max_val + margen)
            else:
                operator_ranges[op_idx] = (0, 1)

        return operator_ranges

    def _setup_hover_cursor(self, fig, ax, line):
        xdata = self.times
        annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )
        annotation.set_visible(False)

        cross_h = ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.6, visible=False)
        cross_v = ax.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.6, visible=False)

        def on_motion(event):
            if event.inaxes != ax:
                annotation.set_visible(False)
                cross_h.set_visible(False)
                cross_v.set_visible(False)
                fig.canvas.draw_idle()
                return

            x = event.xdata
            if x is None:
                return

            ydata = line.get_ydata()
            idx = np.abs(xdata - x).argmin()
            x_val = xdata[idx]
            y_val = ydata[idx]

            annotation.xy = (x_val, y_val)
            annotation.set_text(f"x={x_val:.4f}\ny={y_val:.6f}")
            annotation.set_visible(True)

            cross_h.set_ydata([y_val, y_val])
            cross_v.set_xdata([x_val, x_val])
            cross_h.set_visible(True)
            cross_v.set_visible(True)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)

    def update_plots(self, closest_key):
        data = self.resultados[closest_key]
        for op_idx in range(len(self.operator_names)):
            y_data = data['expect_values'][op_idx]
            
            # Limitar compresión a máximo de 10 en visualización
            is_compresion = 'compresión' in self.operator_names[op_idx].lower()
            if is_compresion:
                y_data = np.clip(y_data, None, 10)
            
            self.lines[op_idx].set_ydata(y_data)
            self.axes[op_idx].set_title(f"{self.operator_names[op_idx]} | ε={closest_key[0]:.3f}, g={closest_key[1]:.3f}")
            self.canvases[op_idx].draw_idle()

        # update comparative only if it exists and indices were found at build time
        if 'comparativa' in self.canvases and getattr(self, 'fotones_idx', None) is not None and getattr(self, 'inv_idx', None) is not None:
            self.lines['comparativa_fotones'].set_ydata(data['expect_values'][self.fotones_idx])
            self.lines['comparativa_inversion'].set_ydata(data['expect_values'][self.inv_idx])
            self.canvases['comparativa'].draw_idle()


class SlidersPanel(ctk.CTkFrame):
    def __init__(self, master, resultados: dict, on_change, closest_init, **grid_kwargs):
        super().__init__(master, fg_color="gray25", corner_radius=8)
        self.resultados = resultados
        self.on_change = on_change
        self.closest_init = closest_init
        self.columnconfigure((1, 3), weight=1)
        self._build()
        self.grid(**grid_kwargs)

    def _build(self):
        eps_values = sorted(set(k[0] for k in self.resultados.keys()))
        g_values = sorted(set(k[1] for k in self.resultados.keys()))

        ctk.CTkLabel(self, text="ε:", font=("Arial", 15, "bold")).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.slider_eps = ctk.CTkSlider(self, from_=eps_values[0], to=eps_values[-1], number_of_steps=len(eps_values)-1, command=lambda v: self._on_slider())
        self.slider_eps.set(self.closest_init[0])
        self.slider_eps.grid(row=0, column=1, sticky="ew", padx=(10, 15), pady=12)

        self.eps_value_label = ctk.CTkLabel(self, text=f"{self.closest_init[0]:.4f}", font=("Arial", 13, "bold"), fg_color="#0d7377", corner_radius=6, width=80)
        self.eps_value_label.grid(row=0, column=2, padx=10, pady=12)

        ctk.CTkLabel(self, text="g:", font=("Arial", 15, "bold")).grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.slider_g = ctk.CTkSlider(self, from_=g_values[0], to=g_values[-1], number_of_steps=len(g_values)-1, command=lambda v: self._on_slider())
        self.slider_g.set(self.closest_init[1])
        self.slider_g.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=12)

        self.g_value_label = ctk.CTkLabel(self, text=f"{self.closest_init[1]:.4f}", font=("Arial", 13, "bold"), fg_color="#0d7377", corner_radius=6, width=80)
        self.g_value_label.grid(row=1, column=2, padx=10, pady=12)

    def _on_slider(self):
        eps = float(self.slider_eps.get())
        lam = float(self.slider_g.get())
        closest = min(self.resultados.keys(), key=lambda x: (x[0]-eps)**2 + (x[1]-lam)**2)
        self.eps_value_label.configure(text=f"{closest[0]:.4f}")
        self.g_value_label.configure(text=f"{closest[1]:.4f}")
        self.on_change(closest)


class GraphApp:
    def __init__(self, resultados: dict, params: dict, parent=None):
        self.resultados = resultados
        self.params = params
        self._own_root = parent is None
        self.window = ctk.CTk() if parent is None else ctk.CTkToplevel(parent)
        self._prepare_data()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _prepare_data(self):
        for k in list(self.resultados.keys()):
            if isinstance(self.resultados[k]["expect_values"], list):
                self.resultados[k]["expect_values"] = np.array(self.resultados[k]["expect_values"])
        calcular_mandel(self.resultados)
        calcular_compresion(self.resultados, self.params["N_ATOMOS"] / 2)

        sample = self.resultados[list(self.resultados.keys())[0]]
        self.n_operators = len(sample["expect_values"])
        self.operator_names = self.params.get("EXPECTED_NAMES") or [f"Operador {i+1}" for i in range(self.n_operators)]
        self.times = np.linspace(self.params["TIEMPO_INICIO"], self.params["TIEMPO_FINAL"], self.params["PASOS"])

    def _build_ui(self):
        self.window.title("Visualizador de Resultados QuTiP")
        self.window.geometry("1400x900")
        self.window.minsize(1000, 700)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=0)
        self.window.rowconfigure(1, weight=1)
        self.window.rowconfigure(2, weight=0)

        self.info = InfoPanel(self.window, self.params, row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.plots = PlotsPanel(self.window, self.resultados, self.operator_names, self.times, row=1, column=0, padx=15, pady=(10, 15), sticky="nsew")
        self.sliders = SlidersPanel(self.window, self.resultados, on_change=self._on_change, closest_init=self.plots.closest_init, row=2, column=0, padx=15, pady=(10, 15), sticky="ew")

    def _on_change(self, closest_key):
        self.plots.update_plots(closest_key)

    def _on_close(self):
        try:
            self.window.destroy()
        except Exception:
            pass

    def mainloop(self):
        if self._own_root:
            self.window.mainloop()


def graficar():
    ventana = VentanaPrincipal()
    ventana.mainloop()


def graph(parent=None):
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    with open(file_path, 'rb') as f:
        resultados = pickle.load(f)

    params = resultados["parametros"]
    resultados.pop("parametros")

    app = GraphApp(resultados, params, parent=parent)
    app.mainloop()


if __name__ == "__main__":
    graph()