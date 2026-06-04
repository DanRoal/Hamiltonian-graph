from qutip import *
import numpy as np
import time
import concurrent.futures as concurr
import pickle
from tkinter import filedialog

def master(N_CAV = 8, N_ATOMOS = 4,TIEMPO_INICIO= 0, TIEMPO_FINAL= 100,PASOS = 250,
           TRABAJADORES = 8,
           EPSILON_IN = 0,EPSILON_OUT = 2,
           LAMDA_IN = 0,LAMDA_OUT = 2, 
           DIVISIONES_EPSILON = 7, DIVISIONES_LAMDA = 30,
           HAMILTONIANO = 'Dicke'):
    global oper
    oper = generar_operadores(N_CAV, N_ATOMOS)

    global valores
    valores = {
        "epsilon_val": np.linspace(EPSILON_IN,EPSILON_OUT,DIVISIONES_EPSILON),
        "lamda_val": np.linspace(LAMDA_IN,LAMDA_OUT,DIVISIONES_LAMDA),
        "lista_tiempos": np.linspace(TIEMPO_INICIO, TIEMPO_FINAL, PASOS),
    }
    #g = lamda / 2*(np.sqrt(N_ATOMOS)) # Acoplamiento
    valores["g_val"] = valores["lamda_val"]/ (2 * np.sqrt(N_ATOMOS))

    global damping
    damping = []
    
    global expected
    expected = [oper["a"].dag()*oper["a"],
                oper["J_z"],
                (1/2)*(oper["a"].dag()*oper["a"] + oper["J_z"]), 
                (oper["a"].dag()*oper["a"])**2,
                oper["J_x"],
                oper["J_x"]**2]
    #Parámetro de mandel

    global expected_names
    expected_names = ["⟨n⟩ (Número de fotones)", 
                      "⟨Jz⟩ (Inversión atómica)", 
                      "pob excitada",
                      "⟨n^2⟩",
                      "⟨J_x⟩",
                      "⟨(J_x)^2⟩",
                      "Parámetro Mandel",
                      "Parámetro Compresión",]

    H_test = oper["a"].dag() * oper["a"] + (0/2) * oper["J_z"] + (0.1/2) * (oper["a"] + oper["a"].dag()) * (oper["J_p"] + oper["J_m"])
    print(f"Dimensión Hilbert: {H_test.dims[0]}")
    print(f"Autovalores min-max: {H_test.eigenenergies()[[0,-1]]}")
    
    calculos(N_CAV, N_ATOMOS, TRABAJADORES, HAMILTONIANO)


def generar_operadores(N_CAV, N_ATOMOS):
    res = {}
    j = N_ATOMOS/2
    
    a = tensor(destroy(N_CAV), qeye(int(2*j +1)))
    res["a"] = a

    #Ahora definimos a los operadores colectivos
    J_z = tensor(qeye(N_CAV), jmat(j, "z"))
    J_p = tensor(qeye(N_CAV), jmat(j, "+"))
    J_m = tensor(qeye(N_CAV), jmat(j, "-"))
    J_x = tensor(qeye(N_CAV), jmat(j, "x"))
    res.update({"J_z":J_z, "J_m":J_m, "J_p":J_p, "J_x":J_x})

    #Generamos estado inicial
    estado_inicial_cavidad = basis(N_CAV, 0)
    estado_inicial_atomico = basis(int(2*j +1), 0)
    res["estado inicial"] =  tensor(estado_inicial_cavidad,estado_inicial_atomico)
    
    return res

def compute_single_tavis(params):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] * oper["J_p"] + oper["a"].dag() * oper["J_m"])
    
    opts = {"nsteps":500000, "rtol":1e-10, "atol":1e-12,}
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected, options=opts)
    
    return (epsilon, g, result)

def compute_single_dicke(params):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] + oper["a"].dag()) * (oper["J_p"] + oper["J_m"])
    
    opts = {"nsteps":500000, "rtol":1e-10, "atol":1e-12,}
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected, options=opts)
    
    return (epsilon, g, result)

def init_trabajador(oper_data, valores_data, expected_data, expected_names_data, damping_data):
    global oper, valores, expected, expected_names, damping
    oper = oper_data
    valores = valores_data
    expected = expected_data
    expected_names = expected_names_data
    damping = damping_data


def calculos(N_cav, N_atomos, TRABAJADORES, HAMILTONIANO):

    nombre_archivo = filedialog.asksaveasfilename()

    param_combinations = [(e, g) for e in valores["epsilon_val"] for g in valores["g_val"]]

    print(f"Total de cálculos: {len(param_combinations)}")
    print("Calculando...")
    
    resultados = {}
    resultados["parametros"] = {
        "N_CAV" : N_cav,
        "N_ATOMOS" : N_atomos,
        "TIEMPO_INICIO": int(valores["lista_tiempos"][0]),
        "TIEMPO_FINAL": int(valores["lista_tiempos"][-1]),
        "PASOS": len(valores["lista_tiempos"]),
        "EPSILON_IN" : int(valores["epsilon_val"][0]),
        "EPSILON_OUT" : int(valores["epsilon_val"][-1]),
        "DIVISIONES_EPSILON" : len(valores["epsilon_val"]),
        "LAMDA_IN" : int(valores["lamda_val"][0]),
        "LAMDA_OUT" : int(valores["lamda_val"][-1]),
        "DIVISIONES_LAMDA": len(valores["lamda_val"]),
        "HAMILTONIANO": HAMILTONIANO,
        "DAMPING_OPERATORS": [str(op) for op in damping] if damping else ["Ninguno"],
        "EXPECTED_NAMES": expected_names,
        }
    inicio = time.time()
    

    if HAMILTONIANO == "Tavis-Cummings":
        with concurr.ProcessPoolExecutor(max_workers=TRABAJADORES, 
                                         initializer=init_trabajador,
                                         initargs= (oper, valores, expected, expected_names, damping)) as executor:

            for i, (epsilon, g, resultados_q) in enumerate(executor.map(compute_single_tavis, param_combinations)):
                resultados[(epsilon, g)] = {'expect_values': resultados_q.expect}

                if (i+1) % 10  == 0:
                    print(f"Completados: {i + 1}/{len(param_combinations)}")
    elif HAMILTONIANO == "Dicke":
        with concurr.ProcessPoolExecutor(max_workers=TRABAJADORES, 
                                         initializer=init_trabajador,
                                         initargs= (oper, valores, expected, expected_names, damping)) as executor:

            for i, (epsilon, g, resultados_q) in enumerate(executor.map(compute_single_dicke, param_combinations)):
                resultados[(epsilon, g)] = {'expect_values': resultados_q.expect}

                if (i+1) % 10  == 0:
                    print(f"Completados: {i + 1}/{len(param_combinations)}")

    fin = time.time()
    print(f"Tardó {fin - inicio:.3f} segundos")


    with open(f'{nombre_archivo}.pkl', 'wb') as f:
        pickle.dump(resultados, f)

    print(f"Resultados guardados en '{nombre_archivo}'")

def calcular_mandel(Resultado:dict[result.expect]):
    for pareja in Resultado:
        n = pareja["expect_values"][0]
        n2 = pareja["expect_values"][3]
        param_mandel = (n2 - n**2 - n)/n 
        np.append(pareja["expect_values"], param_mandel)
    
def calcular_compresion(Resultado:dict[result.expect], j):
    for pareja in Resultado:
        Jx = pareja["expect_values"][4]
        Jx2 = pareja["expect_values"][5]
        
        # Squeezing sin normalizar: sqrt(2*j) * sqrt(<J_x^2> - <J_x>^2)
        delta_jx_squared = np.maximum(Jx2 - Jx**2, 0)
        delta_jx = np.sqrt(delta_jx_squared)
        param_compresion = np.sqrt(2*j) * delta_jx
        np.append(pareja["expect_values"], param_compresion)

    

