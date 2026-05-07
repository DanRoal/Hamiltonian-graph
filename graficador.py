import pickle
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from tkinter import filedialog

def graph():

    # Cargar resultados precalculados
    file_path = filedialog.askopenfilename()
    with open(file_path, 'rb') as f:
        resultados = pickle.load(f)
    
    N_CAV_FILE = resultados["parametros"]["N_CAV"]
    N_ATOMOS_FILE = resultados["parametros"]["N_ATOMOS"]
    TIEMPO_INICIO_FILE = resultados["parametros"]["TIEMPO_INICIO"]
    TIEMPO_FINAL_FILE = resultados["parametros"]["TIEMPO_FINAL"]
    PASOS_FILE = resultados["parametros"]["PASOS"]
    EPSILON_IN_FILE = resultados["parametros"]["EPSILON_IN"]
    EPSILON_OUT_FILE = resultados["parametros"]["EPSILON_OUT"]
    DIVISIONES_EPSILON_FILE = resultados["parametros"]["DIVISIONES_EPSILON"]
    DIVISIONES_LAMDA_FILE = resultados["parametros"]["DIVISIONES_LAMDA"]
    LAMDA_IN_FILE = resultados["parametros"]["LAMDA_IN"]
    LAMDA_OUT_FILE = resultados["parametros"]["LAMDA_OUT"]

    times = np.linspace(TIEMPO_INICIO_FILE, TIEMPO_FINAL_FILE, PASOS_FILE)

    fig = plt.figure(figsize=(8, 6))
    ax1 = plt.subplot(111)
    plt.subplots_adjust(bottom=0.25)

    resultados.pop("parametros")


    # Encontrar los rangos de TODOS los datos
    n_fotones_values = [data['n_fotones'] for data in resultados.values()]
    j_z_values = [data['j_z'] for data in resultados.values()]

    n_fotones_min = min(np.min(arr) for arr in n_fotones_values)
    n_fotones_max = max(np.max(arr) for arr in n_fotones_values)
    j_z_min = min(np.min(arr) for arr in j_z_values)
    j_z_max = max(np.max(arr) for arr in j_z_values)
    # Valores iniciales - encontrar el más cercano a (1.0, 1.0)
    eps_init, g_init = 1.0, 0.25
    closest_init = min(resultados.keys(), 
                       key=lambda x: (x[0]-eps_init)**2 + (x[1]-g_init)**2)
    data = resultados[closest_init]

    # Eje para fotones
    line1, = ax1.plot(times, data['n_fotones'], 'b-', label=r"$\langle n \rangle$ (Fotones)")
    ax1.set_xlabel("Tiempo", fontsize=14)
    ax1.set_ylabel("Número de fotones", color='b', fontsize=14)
    ax1.tick_params(axis='y', labelcolor='b')

    # Establecer límites de eje Y1 (fotones)
    margen = 0.1
    ax1.set_ylim(n_fotones_min - margen*(n_fotones_max-n_fotones_min), 
                 n_fotones_max + margen*(n_fotones_max-n_fotones_min))

    # Eje espejo para Jz
    ax2 = ax1.twinx()
    line2, = ax2.plot(times, data['j_z'], 'r--', label=r"$\langle J_z \rangle$ (Inversión)")
    ax2.set_ylabel("Inversión atómica", color='r', fontsize=14)
    ax2.tick_params(axis='y', labelcolor='r')

    # Establecer límites de eje Y2 (inversión)
    ax2.set_ylim(j_z_min - margen*(j_z_max-j_z_min), 
                 j_z_max + margen*(j_z_max-j_z_min))

    # Sliders
    ax_eps = plt.axes([0.2, 0.15, 0.6, 0.03])
    ax_lam = plt.axes([0.2, 0.08, 0.6, 0.03])

    eps_values = sorted(set(k[0] for k in resultados.keys()))
    g_values = sorted(set(k[1] for k in resultados.keys()))

    slider_eps = Slider(ax_eps, 'epsilon', eps_values[0], eps_values[-1], 
                    valinit=closest_init[0], valstep=(eps_values[-1]-eps_values[0])/(len(eps_values)-1))
    slider_lam = Slider(ax_lam, 'g (lambda/2√N)', g_values[0], g_values[-1], 
                    valinit=closest_init[1], valstep=(g_values[-1]-g_values[0])/(len(g_values)-1))

    def update(val):
        eps = slider_eps.val
        lam = slider_lam.val

        # Encontrar el valor más cercano
        closest = min(resultados.keys(), key=lambda x: (x[0]-eps)**2 + (x[1]-lam)**2)
        data = resultados[closest]

        line1.set_ydata(data['n_fotones'])
        line2.set_ydata(data['j_z'])

        # Actualizar títulos con valores actuales
        ax1.set_title(f"Intercambio de energía: ε={closest[0]:.3f}, g={closest[1]:.3f}")
        fig.canvas.draw_idle()

    slider_eps.on_changed(update)
    slider_lam.on_changed(update)

    plt.show()

if __name__ == "__main__":
    graph()