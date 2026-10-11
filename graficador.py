import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import customtkinter as ctk
from tkinter import filedialog

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
    def __init__(self, master, resultados: dict, operator_names: list, operator_indices: list, times: np.ndarray, **grid_kwargs):
        super().__init__(master)
        self.resultados = resultados
        self.operator_names = list(operator_names)
        self.operator_indices = list(operator_indices)
        self.series_indices = dict(zip(operator_names, operator_indices))
        self.times = times
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.lines = {}
        self.axes = {}
        self.canvases = {}
        self.tabs = {}
        self.plot_keys = {}
        self.visible_names = []
        self.current_name = None
        self.available_operator_names = list(operator_names)
        self.closest_init = min(
            self.resultados.keys(),
            key=lambda key: (key[0] - 1.0) ** 2 + (key[1] - 0.25) ** 2,
        )
        self.current_key = self.closest_init
        self.operator_ranges = self._compute_operator_ranges()
        self._build()
        self.grid(**grid_kwargs)

    def destroy(self):
        for ax in self.axes.values():
            plt.close(ax.figure)
        super().destroy()

    def _build(self):
        self.tab_buttons = ctk.CTkSegmentedButton(
            self,
            values=[],
            command=self._select_tab,
            fg_color="gray30",
            selected_color="#0d7377",
            selected_hover_color="#14919b",
        )
        self.tab_buttons.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.content = ctk.CTkFrame(self, fg_color="gray20")
        self.content.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(self.content, text="No hay gráficas seleccionadas.")

    def set_visible(self, operator_names: list, operator_indices: list):
        current_name = self.tab_buttons.get()
        self.operator_names = list(operator_names)
        self.operator_indices = list(operator_indices)
        self.series_indices = dict(zip(operator_names, operator_indices))
        self.visible_names = self.operator_names
        self.tab_buttons.configure(values=self.visible_names)

        if not self.visible_names:
            if self.current_name in self.tabs:
                self.tabs[self.current_name].grid_forget()
            self.current_name = None
            self.empty_label.grid(row=0, column=0, sticky="nsew")
            return

        self.empty_label.grid_forget()
        selected_name = current_name if current_name in self.visible_names else self.visible_names[0]
        self.tab_buttons.set(selected_name)
        self._show_tab(selected_name)

    def _select_tab(self, name):
        if name in self.visible_names:
            self._show_tab(name)

    def _show_tab(self, name):
        if self.current_name != name and self.current_name in self.tabs:
            self.tabs[self.current_name].grid_forget()

        is_new_plot = name not in self.tabs
        if is_new_plot:
            self._create_plot(name)
        elif self.plot_keys[name] != self.current_key:
            self._update_plot(name, self.current_key)
            self.canvases[name].draw_idle()

        tab = self.tabs[name]
        tab.grid(row=0, column=0, sticky="nsew")
        self.current_name = name

    def save_current_plot(self):
        plot_name = self.current_name
        if plot_name is None or plot_name not in self.tabs:
            return

        epsilon, coupling = self.current_key
        safe_name = "".join(
            "_" if character in '<>:"/\\|?*' else character
            for character in plot_name
        ).strip(" .")
        initial_name = (
            f"{safe_name}_epsilon_{epsilon:.3f}_g_{coupling:.3f}.png"
        )
        file_path = filedialog.asksaveasfilename(
            title="Descargar gráfica",
            initialfile=initial_name,
            defaultextension=".png",
            filetypes=[
                ("Imagen PNG", "*.png"),
                ("Documento PDF", "*.pdf"),
                ("Imagen SVG", "*.svg"),
            ],
        )
        if not file_path:
            return

        self.axes[plot_name].figure.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight",
        )

    def _create_plot(self, name):
        series_idx = self.series_indices[name]
        tab = ctk.CTkFrame(self.content, fg_color="gray20")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
        ax.set_facecolor('white')

        data = self.resultados[self.current_key]
        y_data = data['expect_values'][series_idx]
        if 'compresión' in name.lower():
            y_data = np.clip(y_data, None, 10)

        line, = ax.plot(self.times, y_data, color='#1f77b4', linewidth=2.5, antialiased=True)
        ax.set_xlabel("Tiempo (unidades arbitrarias)", fontsize=15, color='black', fontweight='bold')
        ax.set_ylabel(name, fontsize=15, color='black', fontweight='bold')
        ax.set_ylim(self.operator_ranges[series_idx])
        ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.7)
        ax.tick_params(colors='black', labelsize=12)
        ax.ticklabel_format(style='plain', useOffset=False)
        ax.yaxis.offsetText.set_visible(False)

        for spine in ax.spines.values():
            spine.set_edgecolor('#cccccc')
            spine.set_linewidth(1.2)

        self._setup_hover_cursor(fig, ax, line)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        ax.set_title(
            f"{name} | ε={self.current_key[0]:.3f}, g={self.current_key[1]:.3f}",
            color='black',
            fontsize=15,
            fontweight='bold',
            pad=15,
        )
        fig.tight_layout()
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.tabs[name] = tab
        self.axes[name] = ax
        self.lines[name] = line
        self.canvases[name] = canvas
        self.plot_keys[name] = self.current_key

    def _update_plot(self, name, closest_key):
        data = self.resultados[closest_key]
        y_data = data['expect_values'][self.series_indices[name]]
        if 'compresión' in name.lower():
            y_data = np.clip(y_data, None, 10)

        self.lines[name].set_ydata(y_data)
        self.axes[name].set_title(
            f"{name} | ε={closest_key[0]:.3f}, g={closest_key[1]:.3f}"
        )
        self.plot_keys[name] = closest_key

    def _compute_operator_ranges(self):
        sample = np.asarray(next(iter(self.resultados.values()))['expect_values'])
        min_values = np.full(sample.shape[0], np.inf)
        max_values = np.full(sample.shape[0], -np.inf)
        for data in self.resultados.values():
            values = np.asarray(data['expect_values'])
            min_values = np.minimum(min_values, np.min(values, axis=1))
            max_values = np.maximum(max_values, np.max(values, axis=1))

        ranges = {}
        for index, name in enumerate(self.available_operator_names):
            min_val = min_values[index]
            max_val = max_values[index]
            if 'compresión' in name.lower():
                max_val = min(max_val, 10)
            margin = 0.1 * (max_val - min_val) if max_val != min_val else 0.5
            ranges[index] = (min_val - margin, max_val + margin)
        return ranges

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
        self.current_key = closest_key
        if self.current_name in self.tabs:
            self._update_plot(self.current_name, closest_key)
            self.canvases[self.current_name].draw_idle()

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
        eps_from, eps_to = self._slider_bounds(eps_values)
        g_from, g_to = self._slider_bounds(g_values)

        ctk.CTkLabel(self, text="ε:", font=("Arial", 15, "bold")).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.slider_eps = ctk.CTkSlider(self, from_=eps_from, to=eps_to, number_of_steps=max(len(eps_values)-1, 1), command=lambda v: self._on_slider())
        self.slider_eps.set(self.closest_init[0])
        self.slider_eps.grid(row=0, column=1, sticky="ew", padx=(10, 15), pady=12)

        self.eps_value_label = ctk.CTkLabel(self, text=f"{self.closest_init[0]:.4f}", font=("Arial", 13, "bold"), fg_color="#0d7377", corner_radius=6, width=80)
        self.eps_value_label.grid(row=0, column=2, padx=10, pady=12)

        ctk.CTkLabel(self, text="g:", font=("Arial", 15, "bold")).grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.slider_g = ctk.CTkSlider(self, from_=g_from, to=g_to, number_of_steps=max(len(g_values)-1, 1), command=lambda v: self._on_slider())
        self.slider_g.set(self.closest_init[1])
        self.slider_g.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=12)

        self.g_value_label = ctk.CTkLabel(self, text=f"{self.closest_init[1]:.4f}", font=("Arial", 13, "bold"), fg_color="#0d7377", corner_radius=6, width=80)
        self.g_value_label.grid(row=1, column=2, padx=10, pady=12)

    @staticmethod
    def _slider_bounds(values):
        if len(values) == 1:
            return values[0] - 0.5, values[0] + 0.5
        return values[0], values[-1]

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
        self.plots: PlotsPanel | None = None
        self.sliders: SlidersPanel | None = None

        if not self.resultados:
            return
        
        self._prepare_data()
        self._build_ui()

    def _prepare_data(self):
        for k in list(self.resultados.keys()):
            if isinstance(self.resultados[k]["expect_values"], list):
                self.resultados[k]["expect_values"] = np.array(self.resultados[k]["expect_values"])

        sample = self.resultados[list(self.resultados.keys())[0]]
        base_values = np.asarray(sample["expect_values"])
        expected_names = list(self.params.get("EXPECTED_NAMES") or [])
        if expected_names and len(expected_names) <= base_values.shape[0]:
            operator_names = _ampliar_nombres_operadores(expected_names, base_values.shape[0])
        else:
            operator_names = [f"Operador {i+1}" for i in range(base_values.shape[0])]

        metricas_derivadas = {
            "Parámetro Mandel": {"labels": ["Parámetro Mandel"], "fn": calcular_mandel},
            "Parámetro Compresión Spin": {"labels": ["Parámetro Compresión Spin"], "fn": lambda r: calcular_compresion_spin(r, self.params["N_ATOMOS"] / 2)},
            "Δq": {"labels": ["Δq", "Δp"], "fn": calcular_fluctuacion_cuadraturas},
            "ξ²_q": {"labels": ["ξ²_q", "ξ²_p"], "fn": calcular_compresion_cuadraturas},
        }

        for nombre, config in metricas_derivadas.items():
            labels = config["labels"]
            if base_values.ndim == 2 and base_values.shape[0] >= 10 and not set(labels).issubset(operator_names):
                config["fn"](self.resultados)
                for label in labels:
                    if label not in operator_names:
                        operator_names.append(label)

        metricas_estado = [
            ("Entropía de Von Neumann", "entropy"),
            ("Pureza", "purity"),
        ]

        for nombre, clave in metricas_estado:
            if nombre not in operator_names and all(clave in resultado for resultado in self.resultados.values()):
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

        self.available_operator_names = operator_names
        self._set_visible_names(
            self.params.get("VISIBLE_EXPECTED", operator_names),
            self.params.get("VISIBLE_METRICS", []),
        )
        self.times = np.linspace(self.params["TIEMPO_INICIO"], self.params["TIEMPO_FINAL"], self.params["PASOS"])

    def _set_visible_names(self, visible_expected, visible_metrics):
        visible_names = set(visible_expected or [])
        visible_names.update(visible_metrics or [])
        self.operator_indices = [
            index for index, name in enumerate(self.available_operator_names)
            if name in visible_names
        ]
        self.operator_names = [
            self.available_operator_names[index] for index in self.operator_indices
        ]

    def update_visibility(self, visible_expected, visible_metrics):
        self._set_visible_names(visible_expected, visible_metrics)
        if self.plots is not None:
            self.plots.set_visible(self.operator_names, self.operator_indices)
        if hasattr(self, "save_button"):
            self.save_button.configure(
                state="normal" if self.operator_names else "disabled"
            )

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.info = InfoPanel(
            self,
            self.params,
            row=0,
            column=0,
            columnspan=2,
            padx=15,
            pady=(15, 10),
            sticky="ew",
        )
        self._render_plots()

    def _render_plots(self):
        if self.plots is None:
            plots = PlotsPanel(
                self,
                self.resultados,
                self.available_operator_names,
                list(range(len(self.available_operator_names))),
                self.times,
                row=1,
                column=0,
                columnspan=2,
                padx=15,
                pady=(10, 15),
                sticky="nsew",
            )
            self.plots = plots
            self.sliders = SlidersPanel(
                self,
                self.resultados,
                on_change=self._on_change,
                closest_init=plots.closest_init,
                row=2,
                column=0,
                padx=(15, 5),
                pady=(10, 15),
                sticky="ew",
            )
            self.save_button = ctk.CTkButton(
                self,
                text="Descargar gráfica",
                command=self.plots.save_current_plot,
                state="normal" if self.operator_names else "disabled",
                width=150,
            )
            self.save_button.grid(
                row=2,
                column=1,
                padx=(5, 15),
                pady=(10, 15),
                sticky="se",
            )

        self.plots.set_visible(self.operator_names, self.operator_indices)

    def _on_change(self, closest_key):
        if self.plots is not None:
            self.plots.update_plots(closest_key)




if __name__ == "__main__":
    pass