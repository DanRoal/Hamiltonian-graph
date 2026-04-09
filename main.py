from interface import *
from qutip import *
import customtkinter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import time
import concurrent.futures as concurr
import pickle
from parametros import *
    



epsilon_val = np.linspace(EPSILON_IN,EPSILON_OUT,DIVISIONES)
lamda_val = np.linspace(LAMDA_IN,LAMDA_OUT,DIVISIONES)
#g = lamda / 2*(np.sqrt(N_ATOMOS)) # Acoplamiento

lista_tiempos = np.linspace(0, TIEMPO, PASOS)


a = tensor([destroy(N_CAV)] + [qeye(2) for _ in range(0,  N_ATOMOS)])


#Definimos a la lista de los operadores individuales:
sigmaz_list = [tensor([qeye(N_CAV)] + [sigmaz() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]
sigmam_list = [tensor([qeye(N_CAV)] + [sigmam() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]
sigmap_list = [tensor([qeye(N_CAV)] + [sigmap() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]


#Ahora definimos a los operadores colectivos
J_z = sum(sigmaz_list)
J_m = sum(sigmam_list)
J_p = J_m.dag()

def compute_single(params):
    """Función serializable para multiprocessing"""
    epsilon, lamda = params
    g = lamda / (2 * np.sqrt(N_ATOMOS))
    
    H = a.dag() * a + (epsilon/2) * J_z + (g/2) * (a * J_p + a.dag() * J_m)
    
    estado_inicial = tensor([basis(N_CAV, 0)] + [basis(2, 0) for _ in range(N_ATOMOS)])
    rho0 = ket2dm(estado_inicial)
    
    result = mesolve(H, rho0, lista_tiempos, c_ops=[], e_ops=[a.dag()*a, J_z])
    
    return (epsilon, lamda, result.expect[0], result.expect[1])



if __name__ == "__main__":

    param_combinations = [(e, l) for e in epsilon_val for l in lamda_val]

    print(f"Total de cálculos: {len(param_combinations)}")
    print("Calculando...")

    resultados = {}
    inicio = time.time()

    with concurr.ProcessPoolExecutor(max_workers=TRABAJADORES) as executor:
        for i, (epsilon, lamda, n_fotones, j_z) in enumerate(executor.map(compute_single, param_combinations)):
            resultados[(epsilon, lamda)] = {
                'n_fotones': n_fotones,
                'j_z': j_z
            }
            if (i + 1) % DIVISIONES == 0:
                print(f"Completados: {i + 1}/{len(param_combinations)}")

    fin = time.time()
    print(f"Tardó {fin - inicio:.3f} segundos")

    nombre_archivo = f"res_cav{N_CAV}_at{N_ATOMOS}_t{TIEMPO}_pas{PASOS}_in{EPSILON_IN}_out{EPSILON_OUT}_div{DIVISIONES}"

    with open(f'Resultados/{nombre_archivo}.pkl', 'wb') as f:
        pickle.dump(resultados, f)

    print(f"Resultados guardados en '{nombre_archivo}'")
