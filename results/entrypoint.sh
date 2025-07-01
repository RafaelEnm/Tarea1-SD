#!/bin/bash
set -e
case "${OPERATION}" in
    "filter")
        echo "Ejecutando exportación y filtrado de datos..."
        python3 mongo_exporter.py
        pig -x local data_filter.pig
        ;;
    "process")
        echo "Ejecutando agregación y visualización de datos..."
        pig -x local data_aggregator.pig
        python3 data_visualizer.py
        ;;
    *)
        echo "Operación no reconocida: ${OPERATION}"; exit 1 ;;
esac