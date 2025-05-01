Tarea 1 - Sistemas Distribuidos 2025
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
