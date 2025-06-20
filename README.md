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
