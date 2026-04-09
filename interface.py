import pickle
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from parametros import *
import tkinter as tk
from tkinter import filedialog
import os
import re


if __name__ == "__main__":

    # Cargar resultados precalculados
    file_path = filedialog.askopenfilename()
    with open(file_path, 'rb') as f:
        resultados = pickle.load(f)

    # Extraer parámetros del nombre del archivo
    filename = os.path.basename(file_path)
    match = re.search(r'res_cav(\d+)_at(\d+)_t(\d+)_pas(\d+)_in([\d.]+)_out([\d.]+)_div(\d+)', filename)
    
    if match:
        N_CAV_FILE = int(match.group(1))
        N_ATOMOS_FILE = int(match.group(2))
        TIEMPO_FILE = int(match.group(3))
        PASOS_FILE = int(match.group(4))
        EPSILON_IN_FILE = float(match.group(5))
        EPSILON_OUT_FILE = float(match.group(6))
        DIVISIONES_FILE = int(match.group(7))
        LAMDA_IN_FILE = EPSILON_IN_FILE
        LAMDA_OUT_FILE = EPSILON_OUT_FILE
    else:
        # Si no coincide, usar valores por defecto
        TIEMPO_FILE = TIEMPO
        PASOS_FILE = PASOS
        EPSILON_IN_FILE = EPSILON_IN
        EPSILON_OUT_FILE = EPSILON_OUT
        DIVISIONES_FILE = DIVISIONES
        LAMDA_IN_FILE = LAMDA_IN
        LAMDA_OUT_FILE = LAMDA_OUT

    times = np.linspace(0, TIEMPO_FILE, PASOS_FILE)

    fig = plt.figure(figsize=(8, 6))
    ax1 = plt.subplot(111)
    plt.subplots_adjust(bottom=0.25)

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

    slider_eps = Slider(ax_eps, 'epsilon', EPSILON_IN_FILE, EPSILON_OUT_FILE, valinit=closest_init[0], valstep=(EPSILON_OUT_FILE-EPSILON_IN_FILE)/(DIVISIONES_FILE-1))
    slider_lam = Slider(ax_lam, 'lamda', LAMDA_IN_FILE, LAMDA_OUT_FILE, valinit=closest_init[1], valstep=(LAMDA_OUT_FILE-LAMDA_IN_FILE)/(DIVISIONES_FILE-1))

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