FROM python:3.10-slim

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl chromium-driver chromium \
    && rm -rf /var/lib/apt/lists/*

# Configura Chrome y ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="$PATH:/usr/bin"

WORKDIR /app

COPY scraper.py .

# Instala dependencias de Python
RUN pip install --no-cache-dir pymongo requests matplotlib folium pandas

CMD ["python", "scraper.py"]