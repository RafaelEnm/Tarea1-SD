#!/bin/bash

echo "=== DIAGNÓSTICO Y CORRECCIÓN DE HADOOP ==="

# 1. Revisar logs del NameNode
echo "📋 Revisando logs del NameNode..."
docker logs tarea2-sd-namenode --tail 50

echo ""
echo "=================================="
echo ""

# 2. Detener todos los servicios
echo "🛑 Deteniendo todos los contenedores..."
docker-compose down

# 3. Limpiar volúmenes de Hadoop (ESTO BORRARÁ DATOS DE HDFS)
echo "🧹 Limpiando volúmenes de Hadoop..."
docker volume rm tarea1-sd_hadoop_namenode 2>/dev/null || true
docker volume rm tarea1-sd_hadoop_datanode 2>/dev/null || true

# 4. Recrear y reiniciar servicios
echo "🚀 Recreando servicios..."
docker-compose up -d

# 5. Esperar y verificar estado
echo "⏳ Esperando 30 segundos para que los servicios se inicialicen..."
sleep 30

# 6. Verificar estado
echo "📊 Verificando estado actual..."
docker-compose ps

echo ""
echo "🔍 Verificando logs del NameNode después del reinicio:"
docker logs tarea2-sd-namenode --tail 20

echo ""
echo "✅ Si el NameNode ahora está 'Up' y 'healthy', puedes continuar."
echo "❌ Si sigue reiniciándose, revisa los logs arriba para más detalles."
