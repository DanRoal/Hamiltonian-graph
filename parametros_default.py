import os

N_CAV = 8 #(truncado)
N_ATOMOS =4
TIEMPO_INICIO = 0
TIEMPO_FINAL = 100
PASOS = 250
try:
    TRABAJADORES = int(os.process_cpu_count()/2)
except:
    TRABAJADORES = 2

EPSILON_IN = 0
EPSILON_OUT = 2
LAMDA_IN = 0
LAMDA_OUT = 2

DIVISIONES_EPSILON = 7
DIVISIONES_LAMDA = 30

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