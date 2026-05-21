import pickle
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkinter import filedialog
import customtkinter as ctk
from interface_graficador import VentanaPrincipal

def graficar():
    ventana = VentanaPrincipal()
    ventana.mainloop()

def graph():
    # Cargar resultados precalculados
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    with open(file_path, 'rb') as f:
        resultados = pickle.load(f)

    params = resultados["parametros"]
    resultados.pop("parametros")
    
    # Extraer parámetros
    N_CAV = params["N_CAV"]
    N_ATOMOS = params["N_ATOMOS"]
    TIEMPO_INICIO = params["TIEMPO_INICIO"]
    TIEMPO_FINAL = params["TIEMPO_FINAL"]
    PASOS = params["PASOS"]
    HAMILTONIANO = params["HAMILTONIANO"]
    DAMPING_OPS = params.get("DAMPING_OPERATORS", ["Ninguno"])
    EXPECTED_NAMES = params.get("EXPECTED_NAMES", None)
    
    times = np.linspace(TIEMPO_INICIO, TIEMPO_FINAL, PASOS)
    
    # Crear ventana principal con customtkinter
    root = ctk.CTk()
    root.title("Visualizador de Resultados QuTiP")
    root.geometry("1400x900")
    root.minsize(1000, 700)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=0)
    
    def on_closing():
        """Limpiar recursos al cerrar la ventana"""
        try:
            plt.close('all')
            root.destroy()
        except:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Panel de información
    info_frame = ctk.CTkFrame(root, fg_color="gray25", corner_radius=8)
    info_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
    info_frame.columnconfigure(0, weight=1)
    
    # Primera línea de información
    info_text = (f"N_cavidad: {N_CAV}  |  N_átomos: {N_ATOMOS}  |  "
                 f"Hamiltoniano: {HAMILTONIANO}")
    ctk.CTkLabel(info_frame, text=info_text, font=("Arial", 14, "bold")).pack(pady=(8, 4))

    damping_text = f"Damping operators: {', '.join(DAMPING_OPS)}"
    ctk.CTkLabel(info_frame, text=damping_text, font=("Arial", 13), text_color="gray").pack(pady=(0, 8))  
    
    # Frame principal con tabs
    tab_frame = ctk.CTkFrame(root)
    tab_frame.grid(row=1, column=0, padx=15, pady=(10, 15), sticky="nsew")
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.rowconfigure(0, weight=1)
    
    # Crear notebook (tabs) con customtkinter
    tabview = ctk.CTkTabview(tab_frame, fg_color="gray20", segmented_button_fg_color="gray30",
                             text_color="white", segmented_button_selected_color="#0d7377",
                             segmented_button_selected_hover_color="#14919b")
    tabview.grid(row=0, column=0, sticky="nsew")
    tabview.columnconfigure(0, weight=1)
    
    # Obtener número de operadores esperados
    sample_data = resultados[list(resultados.keys())[0]]
    
    # Compatibilidad con formato antiguo y nuevo
    if 'expect_values' in sample_data:
        n_operators = len(sample_data['expect_values'])
        use_new_format = True
    else:
        # Formato antiguo con 'n_fotones' y 'j_z'
        n_operators = 2
        use_new_format = False
    
    # Usar nombres de operadores si existen
    if EXPECTED_NAMES:
        operator_names = EXPECTED_NAMES
    else:
        operator_names = [f"Operador {i+1}" for i in range(n_operators)]
    
    # Crear datos para minmax
    all_values = []
    for data in resultados.values():
        if use_new_format:
            for arr in data['expect_values']:
                all_values.extend(arr)
        else:
            all_values.extend(data['n_fotones'])
            all_values.extend(data['j_z'])
    
    min_val = min(all_values)
    max_val = max(all_values)
    margen = 0.05 * (max_val - min_val) if (max_val - min_val) != 0 else 0.5
    
    # Valores iniciales
    eps_init, g_init = 1.0, 0.25
    closest_init = min(resultados.keys(), 
                       key=lambda x: (x[0]-eps_init)**2 + (x[1]-g_init)**2)
    
    eps_values = sorted(set(k[0] for k in resultados.keys()))
    g_values = sorted(set(k[1] for k in resultados.keys()))
    
    # Variables globales para actualización
    current_state = {'closest': closest_init}
    lines = {}
    axes = {}
    canvases = {}
    
    # Detectar si existen los operadores de fotones e inversión atómica
    has_fotones = any('fotones' in name.lower() for name in operator_names)
    has_inversion = any('inversión' in name.lower() or 'inversion' in name.lower() for name in operator_names)
    fotones_idx = next((i for i, name in enumerate(operator_names) if 'fotones' in name.lower()), None)
    inversion_idx = next((i for i, name in enumerate(operator_names) if 'inversión' in name.lower() or 'inversion' in name.lower()), None)
    
    # Colores profesionales más suaves para las líneas
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Crear pestaña comparativa si existen ambos operadores
    if has_fotones and has_inversion:
        tab_comparativa = tabview.add("Comparativa")
        tab_comparativa.columnconfigure(0, weight=1)
        tab_comparativa.rowconfigure(0, weight=1)
        
        fig_comp, ax1_comp = plt.subplots(figsize=(12, 6), facecolor='white')
        ax1_comp.set_facecolor('white')
        
        data_comp = resultados[closest_init]
        if use_new_format:
            line_fotones_comp, = ax1_comp.plot(times, data_comp['expect_values'][fotones_idx], 
                                               color='#1f77b4', linewidth=2.5, antialiased=True, label='Fotones')
        else:
            line_fotones_comp, = ax1_comp.plot(times, data_comp['n_fotones'], 
                                               color='#1f77b4', linewidth=2.5, antialiased=True, label='Fotones')
        
        ax1_comp.set_xlabel("Tiempo (unidades arbitrarias)", fontsize=15, color='black', fontweight='bold')
        ax1_comp.set_ylabel("⟨n⟩ (Número de fotones)", fontsize=15, color='#1f77b4', fontweight='bold')
        ax1_comp.tick_params(axis='y', labelcolor='#1f77b4', labelsize=12)
        ax1_comp.tick_params(axis='x', labelsize=12, colors='black')
        ax1_comp.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.7)
        
        # Eje gemelo para inversión
        ax2_comp = ax1_comp.twinx()
        ax2_comp.set_facecolor('white')
        
        if use_new_format:
            line_inversion_comp, = ax2_comp.plot(times, data_comp['expect_values'][inversion_idx], 
                                                  color='#d62728', linewidth=2.5, antialiased=True, linestyle='--', label='Inversión')
        else:
            line_inversion_comp, = ax2_comp.plot(times, data_comp['j_z'], 
                                                  color='#d62728', linewidth=2.5, antialiased=True, linestyle='--', label='Inversión')
        
        ax2_comp.set_ylabel("⟨J_z⟩ (Inversión atómica)", fontsize=15, color='#d62728', fontweight='bold')
        ax2_comp.tick_params(axis='y', labelcolor='#d62728', labelsize=12)
        
        # Mejorar spines
        for spine in ax1_comp.spines.values():
            spine.set_edgecolor('#cccccc')
            spine.set_linewidth(1.2)
        for spine in ax2_comp.spines.values():
            spine.set_edgecolor('#cccccc')
            spine.set_linewidth(1.2)
        
        ax1_comp.set_title(f"Intercambio de energía | ε={closest_init[0]:.3f}, g={closest_init[1]:.3f}", 
                          color='black', fontsize=15, fontweight='bold', pad=15)
        
        # Calcular rangos para ambos ejes
        if use_new_format:
            fotones_values = [data['expect_values'][fotones_idx] for data in resultados.values()]
            inversion_values = [data['expect_values'][inversion_idx] for data in resultados.values()]
        else:
            fotones_values = [data['n_fotones'] for data in resultados.values()]
            inversion_values = [data['j_z'] for data in resultados.values()]
        
        fotones_min = min(np.min(arr) for arr in fotones_values)
        fotones_max = max(np.max(arr) for arr in fotones_values)
        inversion_min = min(np.min(arr) for arr in inversion_values)
        inversion_max = max(np.max(arr) for arr in inversion_values)
        
        margen_fotones = 0.1 * (fotones_max - fotones_min) if (fotones_max - fotones_min) != 0 else 0.5
        margen_inversion = 0.1 * (inversion_max - inversion_min) if (inversion_max - inversion_min) != 0 else 0.5
        
        ax1_comp.set_ylim(fotones_min - margen_fotones, fotones_max + margen_fotones)
        ax2_comp.set_ylim(inversion_min - margen_inversion, inversion_max + margen_inversion)
        
        canvas_comp = FigureCanvasTkAgg(fig_comp, master=tab_comparativa)
        canvas_comp.draw()
        fig_comp.tight_layout()
        canvas_comp.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        canvases['comparativa'] = canvas_comp
        axes['comparativa_1'] = ax1_comp
        axes['comparativa_2'] = ax2_comp
        lines['comparativa_fotones'] = line_fotones_comp
        lines['comparativa_inversion'] = line_inversion_comp
    
    # Crear una pestaña por operador
    for op_idx in range(n_operators):
        tab_frame_content = tabview.add(operator_names[op_idx])
        tab_frame_content.columnconfigure(0, weight=1)
        tab_frame_content.rowconfigure(0, weight=1)

        fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
        ax.set_facecolor('white')
        axes[op_idx] = ax

        data = resultados[closest_init]
        if use_new_format:
            line, = ax.plot(times, data['expect_values'][op_idx], color=colors[op_idx % len(colors)], 
                          linewidth=2.5, antialiased=True)
        else:
            if op_idx == 0:
                line, = ax.plot(times, data['n_fotones'], color=colors[op_idx % len(colors)], 
                              linewidth=2.5, antialiased=True)
            else:
                line, = ax.plot(times, data['j_z'], color=colors[op_idx % len(colors)], 
                              linewidth=2.5, antialiased=True)
        lines[op_idx] = line

        ax.set_xlabel("Tiempo (unidades arbitrarias)", fontsize=15, color='black', fontweight='bold')
        ax.set_ylabel(f"{operator_names[op_idx]}", fontsize=15, color='black', fontweight='bold')
        ax.set_ylim(min_val - margen, max_val + margen)
        
        # Mejorar grid
        ax.grid(True, alpha=0.3, color='gray', linestyle='--', linewidth=0.7)
        ax.tick_params(colors='black', labelsize=12)
        
        # Mejorar spines
        for spine in ax.spines.values():
            spine.set_edgecolor('#cccccc')
            spine.set_linewidth(1.2)
        
        ax.set_title(f"{operator_names[op_idx]} | ε={closest_init[0]:.3f}, g={closest_init[1]:.3f}", 
                    color='black', fontsize=15, fontweight='bold', pad=15)

        canvas = FigureCanvasTkAgg(fig, master=tab_frame_content)
        canvases[op_idx] = canvas
        canvas.draw()
        fig.tight_layout()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)    
    
    # Frame para sliders
    slider_frame = ctk.CTkFrame(root, fg_color="gray25", corner_radius=8)
    slider_frame.grid(row=2, column=0, padx=15, pady=(10, 15), sticky="ew")
    slider_frame.columnconfigure((1, 3), weight=1)
    
    # Slider epsilon
    eps_label = ctk.CTkLabel(slider_frame, text="ε:", font=("Arial", 15, "bold"))
    eps_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")
    
    slider_eps = ctk.CTkSlider(slider_frame, from_=eps_values[0], to=eps_values[-1],
                               number_of_steps=len(eps_values)-1, command=lambda val: update())
    slider_eps.set(closest_init[0])
    slider_eps.grid(row=0, column=1, sticky="ew", padx=(10, 15), pady=12)
    
    eps_value_label = ctk.CTkLabel(slider_frame, text=f"{closest_init[0]:.4f}", 
                                    font=("Arial", 13, "bold"), fg_color="#0d7377", 
                                    corner_radius=6, width=80)
    eps_value_label.grid(row=0, column=2, padx=10, pady=12)
    
    # Slider g
    g_label = ctk.CTkLabel(slider_frame, text="g:", font=("Arial", 15, "bold"))
    g_label.grid(row=1, column=0, padx=15, pady=12, sticky="w")
    
    slider_g = ctk.CTkSlider(slider_frame, from_=g_values[0], to=g_values[-1],
                             number_of_steps=len(g_values)-1, command=lambda val: update())
    slider_g.set(closest_init[1])
    slider_g.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=12)
    
    g_value_label = ctk.CTkLabel(slider_frame, text=f"{closest_init[1]:.4f}", 
                                  font=("Arial", 13, "bold"), fg_color="#0d7377", 
                                  corner_radius=6, width=80)
    g_value_label.grid(row=1, column=2, padx=10, pady=12)
    
    def update():
        eps = slider_eps.get()
        lam = slider_g.get()
        
        # Encontrar valor más cercano
        closest = min(resultados.keys(), 
                     key=lambda x: (x[0]-eps)**2 + (x[1]-lam)**2)
        
        # Actualizar labels de valores
        eps_value_label.configure(text=f"{closest[0]:.4f}")
        g_value_label.configure(text=f"{closest[1]:.4f}")
        
        if closest != current_state['closest']:
            current_state['closest'] = closest
            data = resultados[closest]
            
            # Actualizar todas las gráficas individuales
            for op_idx in range(n_operators):
                if use_new_format:
                    lines[op_idx].set_ydata(data['expect_values'][op_idx])
                else:
                    if op_idx == 0:
                        lines[op_idx].set_ydata(data['n_fotones'])
                    else:
                        lines[op_idx].set_ydata(data['j_z'])
                axes[op_idx].set_title(f"{operator_names[op_idx]} | ε={closest[0]:.3f}, g={closest[1]:.3f}", 
                                      color='black', fontsize=15, fontweight='bold')
                canvases[op_idx].draw_idle()
            
            # Actualizar gráfica comparativa si existe
            if has_fotones and has_inversion:
                if use_new_format:
                    lines['comparativa_fotones'].set_ydata(data['expect_values'][fotones_idx])
                    lines['comparativa_inversion'].set_ydata(data['expect_values'][inversion_idx])
                else:
                    lines['comparativa_fotones'].set_ydata(data['n_fotones'])
                    lines['comparativa_inversion'].set_ydata(data['j_z'])
                
                axes['comparativa_1'].set_title(f"Intercambio de energía | ε={closest[0]:.3f}, g={closest[1]:.3f}", 
                                               color='black', fontsize=15, fontweight='bold')
                canvases['comparativa'].draw_idle()
    
    root.mainloop()

if __name__ == "__main__":
    graph()