import pickle
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

N_cav = 10
N_atomos = 5
tiempo = 50
pasos = 500
divisiones = 20

# Cargar resultados precalculados
with open('resultados_precalculados.pkl', 'rb') as f:
    resultados = pickle.load(f)

times = np.linspace(0, tiempo, pasos)

fig, ax1 = plt.subplots(figsize=(8, 5))

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
ax_eps = plt.axes([0.2, 0.35, 0.6, 0.03])
ax_lam = plt.axes([0.2, 0.28, 0.6, 0.03])

slider_eps = Slider(ax_eps, 'epsilon', 0, 2, valinit=closest_init[0], valstep=2/divisiones)
slider_lam = Slider(ax_lam, 'lamda', 0.1, 2, valinit=closest_init[1], valstep=1.9/divisiones)

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