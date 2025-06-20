# HRIEO---RF
Repositorio para resolver el problema HRIEO con un enfoque Relax and Fix

En este repositorio se encuentran los códigos para resolver el problema HRIEO con un enfoque exacto (MILP) o un enfoque no exacto con Relax&Fix (RF).

En la carpeta percentiles se encuentra una carpeta por cada percentil. Cada una contiene instancias para una fecha concreta de 2 a 12 dams.

Para crear nuevas instancias se debe usar el código create_json.py, cargando el archivo historical_data.pickle y la carpeta de archivos constants_edited.

En la carpeta graphs se encuentran los resultados de la experimentación con los archivos de datos de la carpeta percentiles, además de dos scripts de código usados para crear gráficas.

Librerías necesarias: PuLP, OS, orloge, json, numpy, matplotlib

Actualizar las rutas de archivos y clases para la correcta ejecución de los códigos

# HRIEO---RF

Repositorio para la resolución del problema HRIEO mediante:

- Enfoque exacto mediante un modelo MILP
- Enfoque no exacto mediante la aplicación del heurístico Relax&Fix

## Estructura del repositorio

- `milp/`: scripts para resolver el MILP
- `relax_and_fix/`: scripts para resolver con Relax&Fix
- `percentiles/`: instancias agrupadas por fechas y número de embalses
- `graphs/`: resultados experimentales y scripts usados para su representación en gráficas
- `create_json.py`: generación de instancias a partir de historical_data.pickle. Necesario importar la carpeta constants_edited

## Librerías necesarias

Este proyecto utiliza las siguientes librerías de Python:

- `pulp`
- `orloge`
- `numpy`
- `pandas`
- `matplotlib`
- `datetime`
- `json`
- `os`

## Notas

- Es necesario actualizar las rutas de archivos e importaciones de clases según el entorno para poder ejecutar los scripts correctamente.

## Autora

Desarrollado por Ana Marcos Rubio en su Trabajo de Fin de Máster.
