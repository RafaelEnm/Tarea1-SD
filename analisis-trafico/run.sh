#!/bin/bash

echo "=== Iniciando proceso completo de análisis de datos de tráfico ==="
echo ""

echo "Paso 1: Exportando datos de MongoDB..."
echo ""
python3 exportar_mongo.py
echo ""

echo "Paso 2: Filtrando datos con Apache Pig..."
echo ""
pig -x local filtrar_data.pig
echo ""

echo "Paso 3: Copiando datos filtrados a directorio de entrada para procesamiento..."
echo ""
# Crear directorio de entrada si no existe
mkdir -p /app/input/alertas_completas
mkdir -p /app/input/atascos_completos

# Copiar datos filtrados
cp /app/results/alertas_completas/alertas_completas.csv /app/input/alertas_completas/
cp /app/results/atascos_completos/atascos_completos.csv /app/input/atascos_completos/

echo "Paso 4: Verificando archivos de entrada..."
ls -la /app/input/alertas_completas/
ls -la /app/input/atascos_completos/

echo "Paso 5: Procesando datos con Apache Pig..."
echo ""
pig -x local procesar_data.pig

echo "Paso 6: Resultados del procesamiento:"
ls -la /app/results/

echo "Paso 7: Generando gráficos de los resultados..."
echo ""
python3 graficar.py

echo ""
echo "=== Proceso completo terminado ==="