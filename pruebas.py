import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# 1. Definición de parámetros y pre-cálculo
puntos = 1000
pasos_parametro = 100  # Cantidad de estados guardados
x = np.linspace(0, 10, puntos)
valores_parametro = np.linspace(0.1, 5.0, pasos_parametro)

# Simulamos la computación pesada guardando cada resultado en una lista
memoria_datos = []
for p in valores_parametro:
    # Aquí iría tu función compleja
    resultado = np.sin(x * p) * np.exp(-x / 5)
    memoria_datos.append(resultado)

# 2. Configuración de la interfaz
fig, ax = plt.subplots()
line, = ax.plot(x, memoria_datos[0], lw=2)
ax.set_ylim(-1.1, 1.1)

fig.subplots_adjust(bottom=0.2)
ax_slider = fig.add_axes([0.2, 0.05, 0.6, 0.03])

# El slider opera sobre los índices (0 a 99)
slider_indice = Slider(
    ax_slider, 
    'Parámetro', 
    0, 
    pasos_parametro - 1, 
    valinit=0, 
    valstep=1  # Forzamos a que sean números enteros
)

# 3. Función de actualización por índice
def update(val):
    idx = int(slider_indice.val)  # El valor del slider es el índice del arreglo
    line.set_ydata(memoria_datos[idx])
    fig.canvas.draw_idle()

slider_indice.on_changed(update)

plt.show()