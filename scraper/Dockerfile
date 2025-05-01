FROM python:3.10-slim

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl chromium-driver chromium \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="$PATH:/usr/bin"

WORKDIR /app

# Copia todos los archivos de código
COPY . .

# Instala dependencias de Python
RUN pip install --no-cache-dir pymongo redis requests matplotlib folium pandas
RUN pip install --no-cache-dir pymongo redis requests matplotlib folium pandas flask

CMD ["python", "scraper.py"]
