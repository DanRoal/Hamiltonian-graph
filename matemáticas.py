from qutip import tensor, qeye, destroy, jmat, basis, coherent, Qobj, mesolve
import numpy as np
import time
import concurrent.futures as concurr
import pickle
import parametros_default

def master(nombre_archivo_dado, HAMILTONIANO='Dicke', inicial = "+j",**config):
    config_defaults = {key: getattr(parametros_default, key) for key in getattr(parametros_default, "nombres", {})}
    config = {**config_defaults, **config}
    config["HAMILTONIANO"] = HAMILTONIANO
    config["inicial"] = inicial

    global nombre_archivo
    nombre_archivo = nombre_archivo_dado


    global oper
    oper = generar_operadores(config["N_CAV"], config["N_ATOMOS"], config["inicial"])


    global valores
    valores = {
        "epsilon_val": np.linspace(config["EPSILON_IN"], config["EPSILON_OUT"], config["DIVISIONES_EPSILON"]),
        "lamda_val": np.linspace(config["LAMDA_IN"], config["LAMDA_OUT"], config["DIVISIONES_LAMDA"]),
        "lista_tiempos": np.linspace(config["TIEMPO_INICIO"], config["TIEMPO_FINAL"], config["PASOS"]),
    }
    valores["g_val"] = valores["lamda_val"] / (2 * np.sqrt(config["N_ATOMOS"]))

    global damping
    damping = []
    
    global expected
    expected = {
        "values": [
            oper["a"].dag()*oper["a"],
            oper["J_z"],
            oper["a"].dag()*oper["a"] + oper["J_z"],
            (oper["a"].dag()*oper["a"])**2,
            oper["J_x"],
            oper["J_x"] * oper["J_x"],
        ],
        "names": [
            "⟨n⟩ (Número de fotones)",
            "⟨J_z⟩ (Inversión atómica)",
            "M = ⟨a^\\dagger a + J_z⟩",
            "⟨n^2⟩",
            "⟨J_x⟩",
            "⟨(J_x)^2⟩",
            "Parámetro Mandel",
            "Parámetro Compresión",
        ],
    }
    calculos(config)


def generar_operadores(N_CAV, N_ATOMOS, inicial):
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
    

    ## Generamos estado inicial ##
    match inicial:
        case "+j":
            estado_inicial_cavidad = basis(N_CAV, 0)
            estado_inicial_atomico = basis(int(2*j +1), 0)
            res["estado inicial"] =  tensor(estado_inicial_cavidad,estado_inicial_atomico)
        case "-j":
            estado_inicial_cavidad = basis(N_CAV, N_ATOMOS)
            estado_inicial_atomico = basis(int(2*j +1), int(2*j))
            res["estado inicial"] =  tensor(estado_inicial_cavidad,estado_inicial_atomico)
        case "alpha":
            alpha = 1
            estado_inicial_cavidad = coherent(N_CAV, alpha)
            estado_inicial_atomico = basis(int(2*j +1), int(2*j))
            res["estado inicial"] =  tensor(estado_inicial_cavidad,estado_inicial_atomico)
        case "superpuesto":
            dim = int(2*j + 1)
            vec = np.zeros(dim, dtype=complex)
            vec[0]    = 1/np.sqrt(2)   # m = +j
            vec[-1]   = 1/np.sqrt(2)   # m = -j
            estado_inicial_atomico = Qobj(vec)
            estado_inicial_atomico.dims = [[dim], [1]]
            estado_inicial_cavidad = basis(N_CAV, 0)
            res["estado inicial"] = tensor(estado_inicial_cavidad, estado_inicial_atomico)
        case "coherente superpuesto":
            alpha = 1
            beta = -1j

            # Reconstruir explícitamente como Qobj con dims correctas
            cav_array = (coherent(N_CAV, alpha).full() + coherent(N_CAV, beta).full())
            estado_inicial_cavidad = Qobj(cav_array)
            estado_inicial_cavidad.dims = [[N_CAV], [1]]
            estado_inicial_cavidad = estado_inicial_cavidad.unit()

            estado_inicial_atomico = basis(int(2*j + 1), int(2*j))

            estado_total = tensor(estado_inicial_cavidad, estado_inicial_atomico)
            estado_total.dims = [[N_CAV, int(2*j + 1)], [1, 1]] 

            res["estado inicial"] = estado_total
    

    return res

def compute_single_tavis(params):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] * oper["J_p"] + oper["a"].dag() * oper["J_m"])
    
    opts = {"nsteps":500000, "rtol":1e-10, "atol":1e-12,}
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected["values"], options=opts)
    
    return (epsilon, g, result)

def compute_single_dicke(params):
    """Función serializable para multiprocessing"""
    epsilon, g = params
    
    H = oper["a"].dag() * oper["a"] + (epsilon/2) * oper["J_z"] + (g/2) * (oper["a"] + oper["a"].dag()) * (oper["J_p"] + oper["J_m"])
    
    opts = {"nsteps":500000, "rtol":1e-10, "atol":1e-12,}
    result = mesolve(H, oper["estado inicial"], valores["lista_tiempos"], c_ops=damping, e_ops=expected["values"], options=opts)
    
    return (epsilon, g, result)

def init_trabajador(oper_data, valores_data, expected_data, damping_data):
    global oper, valores, expected, damping
    oper = oper_data
    valores = valores_data
    expected = expected_data
    damping = damping_data
    #queue = queue_data


def calculos(config):

    param_combinations = [(e, g) for e in valores["epsilon_val"] for g in valores["g_val"]]

    print(f"Total de cálculos: {len(param_combinations)}")
    print("Calculando...")
    
    resultados = {}
    resultados["parametros"] = {
        "N_CAV" : config["N_CAV"],
        "N_ATOMOS" : config["N_ATOMOS"],
        "TIEMPO_INICIO": int(valores["lista_tiempos"][0]),
        "TIEMPO_FINAL": int(valores["lista_tiempos"][-1]),
        "PASOS": len(valores["lista_tiempos"]),
        "EPSILON_IN" : int(valores["epsilon_val"][0]),
        "EPSILON_OUT" : int(valores["epsilon_val"][-1]),
        "DIVISIONES_EPSILON" : len(valores["epsilon_val"]),
        "LAMDA_IN" : int(valores["lamda_val"][0]),
        "LAMDA_OUT" : int(valores["lamda_val"][-1]),
        "DIVISIONES_LAMDA": len(valores["lamda_val"]),
        "HAMILTONIANO": config["HAMILTONIANO"],
        "DAMPING_OPERATORS": [str(op) for op in damping] if damping else ["Ninguno"],
        "EXPECTED_NAMES": expected["names"],
        "INITIAL": config["inicial"]
        }
    inicio = time.time()
    
    compute_fn = compute_single_tavis if config["HAMILTONIANO"] == "Tavis-Cummings" else compute_single_dicke

    with concurr.ProcessPoolExecutor(max_workers=config["TRABAJADORES"], 
                                     initializer=init_trabajador,
                                     initargs= (oper, valores, expected, damping)) as executor:
        for i, (epsilon, g, resultados_q) in enumerate(executor.map(compute_fn, param_combinations)):
            resultados[(epsilon, g)] = {'expect_values': resultados_q.expect}
            if (i+1) % 10  == 0:
                print(f"Completados: {i + 1}/{len(param_combinations)}")


    fin = time.time()
    print(f"Tardó {fin - inicio:.3f} segundos")


    with open(f'{nombre_archivo}.pkl', 'wb') as f:
        pickle.dump(resultados, f)

    print(f"Resultados guardados en '{nombre_archivo}'")
