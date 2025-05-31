#!/bin/bash

echo "=== Pipeline de Procesamiento de Datos - Tarea 2 SD ==="

# Esperar a que Hadoop esté disponible
echo "⏳ Esperando a que Hadoop esté disponible..."
while ! hdfs dfsadmin -report &> /dev/null; do
    echo "   Hadoop no está listo, esperando 10 segundos..."
    sleep 10
done

echo "✅ Hadoop está disponible"

# Crear directorios en HDFS si no existen
echo "📁 Creando directorios en HDFS..."
hdfs dfs -mkdir -p /input
hdfs dfs -mkdir -p /output

# Limpiar directorios de salida anteriores
echo "🧹 Limpiando resultados anteriores..."
hdfs dfs -rm -r /output/* 2>/dev/null || true

# Copiar archivo CSV a HDFS
echo "📤 Copiando datos a HDFS..."
if [ -f "/input/waze_incidents.csv" ]; then
    hdfs dfs -put /input/waze_incidents.csv /input/
    echo "✅ Archivo CSV copiado a HDFS"
else
    echo "❌ Error: No se encontró el archivo /input/waze_incidents.csv"
    echo "   Asegúrate de ejecutar primero el exportador de datos"
    exit 1
fi

# Verificar que el archivo esté en HDFS
echo "📋 Verificando archivo en HDFS..."
hdfs dfs -ls /input/

# Ejecutar script de Pig
echo "🐷 Ejecutando script de Pig..."
pig -f /scripts/process_incidents.pig

# Verificar resultados
echo "📊 Verificando resultados generados..."
echo "Archivos de salida en HDFS:"
hdfs dfs -ls /output/

# Copiar resultados a sistema local para revisión
echo "📥 Copiando resultados al sistema local..."
hdfs dfs -get /output/* /output/ 2>/dev/null || true

echo "✅ Pipeline completado!"
echo "📁 Los resultados están disponibles en:"
echo "   - HDFS: /output/"
echo "   - Local: /output/"

# Mostrar primeras líneas de cada resultado
echo ""
echo "=== PREVIEW DE RESULTADOS ==="
for dir in /output/*/; do
    if [ -d "$dir" ]; then
        echo ""
        echo "--- $(basename "$dir") ---"
        find "$dir" -name "part-*" -type f | head -1 | xargs head -10 2>/dev/null || echo "No se pudieron leer los datos"
    fi
done