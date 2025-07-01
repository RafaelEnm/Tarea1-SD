# analisis-trafico/scraper/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y dos2unix && \
    apt-get clean

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# scripts y archivos de configuración
COPY api_server.py json_loader.py traffic_generator.py utility_functions.py waze_scraper.py zipf_generator.py ./
COPY redis.conf ./
COPY entrypoint.sh ./

# Crear directorio de datos
RUN mkdir -p /app/data

# Hacer ejecutable el script de entrada
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

# Punto de entrada que ejecuta según la variable de entorno OPERATION
ENTRYPOINT ["./entrypoint.sh"]