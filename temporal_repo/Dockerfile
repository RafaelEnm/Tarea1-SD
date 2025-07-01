# analisis-trafico/temporal_repo/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CAMBIOS REALIZADOS ---
# Copiar el script 
COPY elastic_uploader.py .

# Crear el directorio de entrada para los datos
RUN mkdir -p /app/input

# Ejecutar el script 
CMD ["python", "elastic_uploader.py"]