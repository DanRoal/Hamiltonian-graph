import os

N_CAV = 8 #(truncado)
N_ATOMOS =4
TIEMPO = 100
PASOS = 250
try:
    TRABAJADORES = os.cpu_count()/2
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
    "TIEMPO": "Tiempo de graficación",
    "PASOS": "Cantidad de pasos",
    "TRABAJADORES": "Cantidad de procesos simultaneos (precaución)",
    "EPSILON_IN" : "Inicio epsilon",
    "EPSILON_OUT" : "Fin epsilon",
    "LAMDA_IN" : "Inicio Lambda",
    "LAMDA_OUT" : "Fin lambda",
    "DIVISIONES_EPSILON" : "Resolución Epsilon",
    "DIVISIONES_LAMDA" : "Resolución Lambda",
}