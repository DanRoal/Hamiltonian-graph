import os

N_CAV = 20 #(truncado)
N_ATOMOS = 5
TIEMPO_INICIO = 0
TIEMPO_FINAL = 50
PASOS = 500
try:
    TRABAJADORES = int(os.process_cpu_count()/2)
except:
    TRABAJADORES = 2

EPSILON_IN = 0.1
EPSILON_OUT = 2
LAMDA_IN = 0
LAMDA_OUT = 2

DIVISIONES_EPSILON = 11
DIVISIONES_LAMDA = 50

nombres = {
    "N_CAV": "Número de fotones en la cavidad",
    "N_ATOMOS": "Número de átomos",
    "TIEMPO_INICIO": "Inicio de tiempo de graficación",
    "TIEMPO_FINAL": "Final de tiempo de graficación",
    "PASOS": "Cantidad de pasos",
    "TRABAJADORES": "Cantidad de procesos simultaneos (precaución)",
    "EPSILON_IN" : "Inicio epsilon",
    "EPSILON_OUT" : "Fin epsilon",
    "DIVISIONES_EPSILON" : "Resolución Epsilon",
    "LAMDA_IN" : "Inicio Lambda",
    "LAMDA_OUT" : "Fin lambda",
    "DIVISIONES_LAMDA" : "Resolución Lambda",
}