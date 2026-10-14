# Hamgraph  
### Un simulador de dinámica de átomos de dos niveles

Los modelos más usados para el modelado de la interacción luz materia son los modelos de Tavis-Cummings y el modelo de Dicke, por lo que tener una aplicación que funcione como campo de pruebas para su dinámica con sitemas de distinto tamaño y distintos parámetros funciona como una herramienta con capacida analítica real haciendo accesible una capacidad de análisis de estos modelos a una población más amplia de investigadores y estudiantes que no necesitarían conocimientos avanzados de programación para poder empezar a hacer investigación sobre el tema.

La idea  de Hamgraph es proveer una plataforma súmamente eficiente que utilice la paralelización de recursos para lograr una  capacidad de análisis previamente solo accesibles con supercomputadoras.

Los hamiltonianos que por ahora están disponibles para simularse son los siguientes:

### Tavis-Cummings

$$ H_T = aˆ{\dagger}a + \epsilon J_z + g (aJ_+ + aˆ\dagger J_-) $$

### Dicke

$$ H_T = aˆ{\dagger}a + \epsilon J_z + g(aˆ\dagger + a)(J_+ + J_-) $$

El programa tiene la posibilidad de simular distintos estados iniciales a la vez que permite calcular una gran cantidad de valores esperados de combinaciones lineales de los operadores de creación y aniquilación bosónicos ($a$ y $aˆ\dagger$) y de spin colectivo ($J_\pm$)

![interfaz](figures/interfaz.png)
