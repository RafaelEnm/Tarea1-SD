# analisis-trafico/results/Dockerfile

FROM openjdk:8-jdk-slim

WORKDIR /app

# Instalar herramientas del sistema y dependencias para Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip wget dos2unix ca-certificates gnupg \
                       build-essential libfreetype6-dev pkg-config libpng-dev && \
    apt-get clean

# Instalar herramientas de MongoDB (para mongoexport)
RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    apt-get clean

# Instalar Apache Pig
RUN wget https://dlcdn.apache.org/pig/pig-0.17.0/pig-0.17.0.tar.gz && \
    tar -xzf pig-0.17.0.tar.gz -C /opt && \
    rm pig-0.17.0.tar.gz && \
    ln -s /opt/pig-0.17.0 /opt/pig

# Configurar PiggyBank
RUN mkdir -p /opt/pig/lib && \
    wget https://repo1.maven.org/maven2/org/apache/pig/piggybank/0.17.0/piggybank-0.17.0.jar -O /opt/pig/lib/piggybank.jar && \
    chmod 644 /opt/pig/lib/*.jar

# Configurar variables de entorno
ENV PIG_HOME=/opt/pig
ENV PATH=$PATH:$PIG_HOME/bin
ENV JAVA_HOME=/usr/local/openjdk-8

# Instalar dependencias Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# scripts y archivos de configuracion 
COPY data_visualizer.py duplicate_checker.py json_analyzer.py mongo_exporter.py ./
COPY data_aggregator.pig data_filter.pig ./
COPY entrypoint.sh ./

# Crear directorios de trabajo
RUN mkdir -p /app/data /app/results /app/input

# Configurar permisos de scripts
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

# Punto de entrada
ENTRYPOINT ["./entrypoint.sh"]