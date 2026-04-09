from interface import *
from qutip import *
import numpy as np
import pickle
import concurrent.futures as concurr
from pathlib import Path
import pickle
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

N_cav = 10
N_atomos = 5
tiempo = 50
pasos = 500

# Configuración de parámetros
epsilon_values = np.linspace(0, 2, 20)
lamda_values = np.linspace(0.1, 2, 20)

def compute_single(params):
    """Función serializable para multiprocessing"""
    epsilon, lamda = params
    g = lamda / (2 * np.sqrt(N_atomos))
    
    # Construir operadores
    a = tensor([destroy(N_cav)] + [qeye(2) for _ in range(N_atomos)])
    sigmaz_list = [tensor([qeye(N_cav)] + [sigmaz() if j == i else qeye(2) 
                   for j in range(N_atomos)]) for i in range(N_atomos)]
    sigmam_list = [tensor([qeye(N_cav)] + [sigmam() if j == i else qeye(2) 
                   for j in range(N_atomos)]) for i in range(N_atomos)]
    
    J_z = sum(sigmaz_list)
    J_m = sum(sigmam_list)
    J_p = J_m.dag()
    
    H = a.dag() * a + (epsilon/2) * J_z + (g/2) * (a * J_p + a.dag() * J_m)
    
    estado_inicial = tensor([basis(N_cav, 0)] + [basis(2, 0) for _ in range(N_atomos)])
    rho0 = ket2dm(estado_inicial)
    
    times = np.linspace(0, tiempo, pasos)
    result = mesolve(H, rho0, times, c_ops=[], e_ops=[a.dag()*a, J_z])
    
    return (epsilon, lamda, result.expect[0], result.expect[1])

if __name__ == "__main__":
    # Generar combinaciones de parámetros
    param_combinations = [(e, l) for e in epsilon_values for l in lamda_values]
    
    print(f"Total de cálculos: {len(param_combinations)}")
    print("Calculando...")
    
    resultados = {}
    
    with concurr.ProcessPoolExecutor(max_workers=10) as executor:
        for i, (epsilon, lamda, n_fotones, j_z) in enumerate(executor.map(compute_single, param_combinations)):
            resultados[(epsilon, lamda)] = {
                'n_fotones': n_fotones,
                'j_z': j_z
            }
            if (i + 1) % 100 == 0:
                print(f"Completados: {i + 1}/{len(param_combinations)}")
    
    # Guardar resultados
    with open('resultados_precalculados.pkl', 'wb') as f:
        pickle.dump(resultados, f)
    
    print("Resultados guardados en 'resultados_precalculados.pkl'")

    # Cargar resultados precalculados
    with open('resultados_precalculados.pkl', 'rb') as f:
        resultados = pickle.load(f)

    times = np.linspace(0, tiempo, pasos)

    fig, (ax1, ax2) = plt.subplots(2, 1)

    # Valores iniciales
    eps_init, lam_init = 1.0, 1.0
    data = resultados[(eps_init, lam_init)]
    line1, = ax1.plot(times, data['n_fotones'])
    line2, = ax2.plot(times, data['j_z'])

    # Sliders
    ax_eps = plt.axes([0.2, 0.35, 0.6, 0.03])
    ax_lam = plt.axes([0.2, 0.30, 0.6, 0.03])

    slider_eps = Slider(ax_eps, 'epsilon', 0, 2, valinit=1.0, step=2/20)
    slider_lam = Slider(ax_lam, 'lamda', 0.1, 2, valinit=1.0, step=1.9/20)

    def update(val):
        eps = slider_eps.val
        lam = slider_lam.val

        # Encontrar el valor más cercano (por si hay redondeo)
        closest = min(resultados.keys(), 
                      key=lambda x: (x[0]-eps)**2 + (x[1]-lam)**2)
        data = resultados[closest]

        line1.set_ydata(data['n_fotones'])
        line2.set_ydata(data['j_z'])
        fig.canvas.draw_idle()

    slider_eps.on_changed(update)
    slider_lam.on_changed(update)

    plt.show()