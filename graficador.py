import pickle
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from tkinter import filedialog

if __name__ == "__main__":

    # Cargar resultados precalculados
    file_path = filedialog.askopenfilename()
    with open(file_path, 'rb') as f:
        resultados = pickle.load(f)
    
    N_CAV_FILE = resultados["parametros"]["N_CAV"]
    N_ATOMOS_FILE = resultados["parametros"]["N_ATOMOS"]
    TIEMPO_FILE = resultados["parametros"]["TIEMPO"]
    PASOS_FILE = resultados["parametros"]["PASOS"]
    EPSILON_IN_FILE = resultados["parametros"]["EPSILON_IN"]
    EPSILON_OUT_FILE = resultados["parametros"]["EPSILON_OUT"]
    DIVISIONES_EPSILON_FILE = resultados["parametros"]["DIVISIONES_EPSILON"]
    DIVISIONES_LAMDA_FILE = resultados["parametros"]["DIVISIONES_LAMDA"]
    LAMDA_IN_FILE = resultados["parametros"]["LAMDA_IN"]
    LAMDA_OUT_FILE = resultados["parametros"]["LAMDA_OUT"]

    times = np.linspace(0, TIEMPO_FILE, PASOS_FILE)

    fig = plt.figure(figsize=(8, 6))
    ax1 = plt.subplot(111)
    plt.subplots_adjust(bottom=0.25)

    resultados.pop("parametros")

    # Valores iniciales - encontrar el más cercano a (1.0, 1.0)
    eps_init, lam_init = 1.0, 1.0
    closest_init = min(resultados.keys(), 
                       key=lambda x: (x[0]-eps_init)**2 + (x[1]-lam_init)**2)
    data = resultados[closest_init]

    # Eje para fotones
    line1, = ax1.plot(times, data['n_fotones'], 'b-', label=r"$\langle n \rangle$ (Fotones)")
    ax1.set_xlabel("Tiempo", fontsize=14)
    ax1.set_ylabel("Número de fotones", color='b', fontsize=14)
    ax1.tick_params(axis='y', labelcolor='b')

    # Eje espejo para Jz
    ax2 = ax1.twinx()
    line2, = ax2.plot(times, data['j_z'], 'r--', label=r"$\langle J_z \rangle$ (Inversión)")
    ax2.set_ylabel("Inversión atómica", color='r', fontsize=14)
    ax2.tick_params(axis='y', labelcolor='r')

    # Sliders
    ax_eps = plt.axes([0.2, 0.15, 0.6, 0.03])
    ax_lam = plt.axes([0.2, 0.08, 0.6, 0.03])

    slider_eps = Slider(ax_eps, 'epsilon', EPSILON_IN_FILE, EPSILON_OUT_FILE, valinit=closest_init[0], valstep=(EPSILON_OUT_FILE-EPSILON_IN_FILE)/(DIVISIONES_EPSILON_FILE-1))
    slider_lam = Slider(ax_lam, 'lamda', LAMDA_IN_FILE, LAMDA_OUT_FILE, valinit=closest_init[1], valstep=(LAMDA_OUT_FILE-LAMDA_IN_FILE)/(DIVISIONES_LAMDA_FILE-1))

    def update(val):
        eps = slider_eps.val
        lam = slider_lam.val

        # Encontrar el valor más cercano
        closest = min(resultados.keys(), 
                      key=lambda x: (x[0]-eps)**2 + (x[1]-lam)**2)
        data = resultados[closest]

        line1.set_ydata(data['n_fotones'])
        line2.set_ydata(data['j_z'])

        # Actualizar títulos con valores actuales
        ax1.set_title(f"Intercambio de energía: ε={closest[0]:.3f}, λ={closest[1]:.3f}")
        fig.canvas.draw_idle()

    slider_eps.on_changed(update)
    slider_lam.on_changed(update)

    plt.show()