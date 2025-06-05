FROM openjdk:8-jdk-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip wget dos2unix ca-certificates gnupg python3-dev build-essential \
                       libfreetype6-dev pkg-config libpng-dev && \
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    apt-get clean

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN wget https://dlcdn.apache.org/pig/pig-0.17.0/pig-0.17.0.tar.gz && \
    tar -xzf pig-0.17.0.tar.gz -C /opt && \
    rm pig-0.17.0.tar.gz && \
    ln -s /opt/pig-0.17.0 /opt/pig

RUN mkdir -p /opt/pig/lib

RUN wget https://repo1.maven.org/maven2/org/apache/pig/piggybank/0.17.0/piggybank-0.17.0.jar -O /opt/pig/lib/piggybank.jar

RUN chmod 644 /opt/pig/lib/*.jar

ENV PIG_HOME=/opt/pig
ENV PATH=$PATH:$PIG_HOME/bin
ENV JAVA_HOME=/usr/local/openjdk-8
ENV HADOOP_HOME=/opt/pig

COPY exportar_mongo.py .
COPY filtrar_data.pig .
COPY procesar_data.pig .
COPY graficar.py .
COPY run.sh .

RUN mkdir -p /app/data
RUN mkdir -p /app/input 
RUN mkdir -p /app/results

RUN dos2unix run.sh && \
    chmod +x run.sh && \
    chmod +x graficar.py

CMD ["./run.sh"]