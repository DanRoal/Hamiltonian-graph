from qutip import *
import numpy as np
import time
import concurrent.futures as concurr
import pickle
from tkinter import filedialog

def master(N_CAV = 8,N_ATOMOS = 4,TIEMPO_INICIO= 0, TIEMPO_FINAL= 100,PASOS = 250,
           TRABAJADORES = 8,
           EPSILON_IN = 0,EPSILON_OUT = 2,
           LAMDA_IN = 0,LAMDA_OUT = 2, 
           DIVISIONES_EPSILON = 7, DIVISIONES_LAMDA = 30,
           HAMILTONIANO = 'Dicke'):
    
    oper = generar_operadores(N_CAV, N_ATOMOS)
    valores = {
        "epsilon_val": np.linspace(EPSILON_IN,EPSILON_OUT,DIVISIONES_EPSILON),
        "lamda_val": np.linspace(LAMDA_IN,LAMDA_OUT,DIVISIONES_LAMDA),
        "lista_tiempos": np.linspace(TIEMPO_INICIO, TIEMPO_FINAL, PASOS),
    }
    #g = lamda / 2*(np.sqrt(N_ATOMOS)) # Acoplamiento
    valores["g_val"] = valores["lamda_val"]/ (2 * np.sqrt(N_ATOMOS))
    
    
    calculos(oper, valores, TRABAJADORES, HAMILTONIANO)
    pass

def generar_operadores(N_CAV, N_ATOMOS):
    res = {}
    
    a = tensor([destroy(N_CAV)] + [qeye(2) for _ in range(0,  N_ATOMOS)])
    res["a"] = a
    
    #Definimos a la lista de los operadores individuales:
    sigmaz_list = [tensor([qeye(N_CAV)] + [sigmaz() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]
    sigmam_list = [tensor([qeye(N_CAV)] + [sigmam() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]
    sigmap_list = [tensor([qeye(N_CAV)] + [sigmap() if j == i else qeye(2) for j in range(N_ATOMOS)]) for i in range(N_ATOMOS)]
    
    #Ahora definimos a los operadores colectivos
    J_z = sum(sigmaz_list)
    J_m = sum(sigmam_list)
    J_p = J_m.dag()
    res.update({"J_z":J_z, "J_m":J_m, "J_p":J_p})

    #Generamos estado inicial
    estado_inicial = ket2dm(tensor([basis(N_CAV, 0)] + [basis(2, 0) for _ in range(N_ATOMOS)]))
    res["estado inicial"] =  estado_inicial
    
    return res




def compute_single_tavis(params, oper, valores, expected, damping):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] * oper["J_p"] + oper["a"].dag() * oper["J_m"])
    
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected)
    
    return (epsilon, g, result.expect[0], result.expect[1])

def compute_single_dicke(params,oper, valores, expected, damping):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] + oper["a"].dag())(oper["J_p"] + oper["J_m"])
    
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected)
    
    return (epsilon, g, result.expect[0], result.expect[1])

def calculos(operadores, valores, TRABAJADORES, HAMILTONIANO):

    nombre_archivo = filedialog.asksaveasfilename()

    param_combinations = [(e, g) for e in valores["epsilon_val"] for g in valores["g_val"]]

    print(f"Total de cálculos: {len(param_combinations)}")
    print("Calculando...")

    resultados = {}
    resultados["parametros"] = {
        "N_CAV" : N_CAV,
        "N_ATOMOS" : N_ATOMOS,
        "TIEMPO" : TIEMPO,
        "PASOS" : PASOS,
        "TRABAJADORES" : TRABAJADORES,
        "EPSILON_IN" : EPSILON_IN,
        "EPSILON_OUT" : EPSILON_OUT,
        "LAMDA_IN" : LAMDA_IN,
        "LAMDA_OUT" : LAMDA_OUT,
        "DIVISIONES_EPSILON" : DIVISIONES_EPSILON,
        "DIVISIONES_LAMDA": DIVISIONES_LAMDA,
        }
    inicio = time.time()

    if HAMILTONIANO == "Tavis-Cummings":
        with concurr.ProcessPoolExecutor(max_workers=TRABAJADORES) as executor:

            for i, (epsilon, lamda, n_fotones, j_z) in enumerate(executor.map(compute_single_tavis, param_combinations)):
                resultados[(epsilon, lamda)] = {
                    'n_fotones': n_fotones,
                    'j_z': j_z
                }
                if (i+1) % 10  == 0:
                    print(f"Completados: {i + 1}/{len(param_combinations)}")
    elif HAMILTONIANO == "Dicke":
        with concurr.ProcessPoolExecutor(max_workers=TRABAJADORES) as executor:

            for i, (epsilon, lamda, n_fotones, j_z) in enumerate(executor.map(compute_single_dicke, param_combinations)):
                resultados[(epsilon, lamda)] = {
                    'n_fotones': n_fotones,
                    'j_z': j_z
                }
                if (i+1) % 10  == 0:
                    print(f"Completados: {i + 1}/{len(param_combinations)}")

    fin = time.time()
    print(f"Tardó {fin - inicio:.3f} segundos")


    with open(f'{nombre_archivo}.pkl', 'wb') as f:
        pickle.dump(resultados, f)

    print(f"Resultados guardados en '{nombre_archivo}'")
