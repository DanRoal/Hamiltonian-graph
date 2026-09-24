import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import customtkinter as ctk

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interface import App


def calcular_mandel(resultado: dict, operator_names: list | None = None):
    for pareja in resultado:
        n = resultado[pareja]["expect_values"][0]
        n2 = resultado[pareja]["expect_values"][3]
        param_mandel = np.divide(
            n2 - n**2 - n,
            n,
            out=np.zeros_like(n, dtype=float),
            where=n != 0,
        )
        resultado[pareja]["expect_values"] = np.vstack([resultado[pareja]["expect_values"], param_mandel])


def calcular_compresion_spin(resultado: dict, j: float, operator_names: list | None = None):
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


def calcular_fluctuacion_cuadraturas(resultado: dict):
    for pareja in resultado:
        q = resultado[pareja]["expect_values"][6]
        q2 = resultado[pareja]["expect_values"][7]
        p = resultado[pareja]["expect_values"][8]
        p2 = resultado[pareja]["expect_values"][9]

        var_q = q2 - q**2
        var_p = p2 - p**2

        fluctuacion_q = np.sqrt(np.maximum(var_q, 0.0))
        fluctuacion_p = np.sqrt(np.maximum(var_p, 0.0))

        resultado[pareja]["expect_values"] = np.vstack([
            resultado[pareja]["expect_values"],
            fluctuacion_q,
            fluctuacion_p,
        ])

def calcular_compresion_cuadraturas(resultado: dict):
    for pareja in resultado:
        q = resultado[pareja]["expect_values"][6]
        q2 = resultado[pareja]["expect_values"][7]
        p = resultado[pareja]["expect_values"][8]
        p2 = resultado[pareja]["expect_values"][9]

        var_q = q2 - q**2
        var_p = p2 - p**2
        xi2_q = 2 * np.maximum(var_q, 0.0)
        xi2_p = 2 * np.maximum(var_p, 0.0)

        resultado[pareja]["expect_values"] = np.vstack([
            resultado[pareja]["expect_values"],
            xi2_q,
            xi2_p,
        ])


def _ampliar_nombres_operadores(operator_names: list, n_series: int) -> list:
    nombres = list(operator_names)
    metricas = [
        "Parámetro Mandel",
        "Parámetro Compresión Spin",
        "Δq",
        "Δp",
        "ξ²_q",
        "ξ²_p",
    ]

    for nombre in metricas:
        if len(nombres) >= n_series:
            break
        if nombre not in nombres:
            nombres.append(nombre)

    while len(nombres) < n_series:
        nombres.append(f"Operador {len(nombres) + 1}")

    return nombres[:n_series]


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


class GraphApp(ctk.CTkScrollableFrame):
    def __init__(self, master, controller: "App"):
        super().__init__(master)
        self.resultados = getattr(controller, "resultados", {})
        self.params = getattr(controller, "parametros", {})

        if not self.resultados:
            return
        
        self._prepare_data()
        self._build_ui()

    def _prepare_data(self):
        for k in list(self.resultados.keys()):
            if isinstance(self.resultados[k]["expect_values"], list):
                self.resultados[k]["expect_values"] = np.array(self.resultados[k]["expect_values"])

        operator_names = list(self.params.get("EXPECTED_NAMES") or [])
        sample = self.resultados[list(self.resultados.keys())[0]]
        base_values = np.asarray(sample["expect_values"])

        # Aunque el archivo ya exista sin flags, la vista debe añadir las métricas derivadas
        # para que aparezcan como pestañas en la carga real del resultado.
        if base_values.ndim == 2 and base_values.shape[0] >= 10:
            if "Parámetro Mandel" not in operator_names:
                calcular_mandel(self.resultados)
                operator_names.append("Parámetro Mandel")
            if "Parámetro Compresión Spin" not in operator_names:
                calcular_compresion_spin(self.resultados, self.params["N_ATOMOS"] / 2)
                operator_names.append("Parámetro Compresión Spin")
            if "Δq" not in operator_names:
                calcular_fluctuacion_cuadraturas(self.resultados)
                operator_names.extend(["Δq", "Δp"])
            if "ξ²_q" not in operator_names:
                calcular_compresion_cuadraturas(self.resultados)
                operator_names.extend(["ξ²_q", "ξ²_p"])

        # Añadir entropía y pureza como series graficables
        metricas_estado = [
            ("Entropía de Von Neumann", "entropy"),
            ("Pureza", "purity"),
        ]

        for nombre, clave in metricas_estado:
            if (
                nombre not in operator_names
                and all(clave in resultado for resultado in self.resultados.values())
            ):
                longitudes_validas = all(
                    len(resultado[clave]) == len(resultado["expect_values"][0])
                    for resultado in self.resultados.values()
                )
                if not longitudes_validas:
                    continue

                for resultado in self.resultados.values():
                    valores = np.asarray(resultado[clave], dtype=float)
                    resultado["expect_values"] = np.vstack([
                        resultado["expect_values"],
                        valores,
                    ])

                operator_names.append(nombre)

        sample = self.resultados[list(self.resultados.keys())[0]]
        self.n_operators = len(sample["expect_values"])
        if not operator_names:
            operator_names = [f"Operador {i+1}" for i in range(self.n_operators)]
        elif len(operator_names) < self.n_operators:
            operator_names = _ampliar_nombres_operadores(operator_names, self.n_operators)

        self.operator_names = operator_names[:self.n_operators]
        self.times = np.linspace(self.params["TIEMPO_INICIO"], self.params["TIEMPO_FINAL"], self.params["PASOS"])

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.info = InfoPanel(self, self.params, row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        self.plots = PlotsPanel(self, self.resultados, self.operator_names, self.times, row=1, column=0, padx=15, pady=(10, 15), sticky="nsew")
        self.sliders = SlidersPanel(self, self.resultados, on_change=self._on_change, closest_init=self.plots.closest_init, row=2, column=0, padx=15, pady=(10, 15), sticky="ew")

    def _on_change(self, closest_key):
        self.plots.update_plots(closest_key)




if __name__ == "__main__":
    pass