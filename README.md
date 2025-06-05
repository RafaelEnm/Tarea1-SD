Tarea 1 - Sistemas Distribuidos 2025
**Nombres:** Diego Hidalgo, Rafael Encina  
**Sección:** 03

Este proyecto implementa un sistema distribuido para la recolección, almacenamiento, consulta y análisis de eventos de tráfico en tiempo real obtenidos desde la API de Waze.

Requisitos
- Docker
- Docker Compose
- Python 3.10+
  
Cómo levantar el proyecto

1. Clonar el repositorio:
   git clone https://github.com/RafaelEnm/Tarea1-SD.git
   cd Tarea1-SD
   
2. Levantar los servicios (Mongo, Redis, Api, Scraper, Query):
  sudo docker-compose up --build

3. Para un análisis a fondo:
  python3 scraper/inspect_json.py (en caso de no detectar Json)
  python3 run scraper/analyze_results.py
Esto procesará los archivos .json generados por el simulador y mostrará estadísticas comparativas entre las políticas de caché

4. Query.py: muestra las primeras 20 filas de datos junto con el total de eventos de la base de datos. (no es necesario su ejecución)

tarea-2 Sistemas Distribuidos 2025 # Sistema de Análisis de Datos de Tráfico

Sistema distribuido para recopilar, almacenar y analizar datos de tráfico en tiempo real usando Waze.

**Nombres:** Diego Hidalgo, Rafael Encina  
**Sección:** 03

## Estructura del Proyecto

```
Tarea2-SD/
├── scraper/              # Recopilación de datos desde Waze
├── analisis-trafico/     # Procesamiento y análisis de datos
└── docker-compose.yml    # Orquestación de servicios con Docker
```
## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/RafaelEnm/Tarea1-SD.git
cd Tarea2-SD
```
Levantar todos los servicios:

```bash
docker compose up -d o docker compose up --build -d
```
## Servicios Disponibles

- **MongoDB** en puerto 27017
- **Redis** en puerto 6379
- **Scraper** para obtener datos de Waze
- **API Server** para consultas en puerto 5000
- **Análisis de tráfico** que procesa y genera reportes

## Comandos Útiles

Ver logs de un servicio:
```bash
docker compose logs [nombre_servicio]
```
Detener servicios:
```bash
docker compose down
```
## Flujo del Sistema

1. **Scraper** extrae datos en tiempo real desde Waze
2. Los datos se almacenan en **MongoDB**
3. **API Server** permite realizar consultas
4. El módulo de **análisis** procesa los datos y genera reportes visuales
