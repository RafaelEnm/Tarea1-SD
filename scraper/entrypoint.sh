#!/bin/bash
# Este comando asegura que el script se detenga si cualquier comando falla
set -e

case "${OPERATION}" in
    "load_json")
        echo "Ejecutando carga de datos JSON..."
        python3 json_loader.py
        ;;
    "scrape")
        echo "Ejecutando scraper de Waze..."
        python3 waze_scraper.py
        ;;
    "server")
        echo "Iniciando servidor API..."
        python3 api_server.py
        ;;
    "generate_traffic")
        echo "Generando tráfico de prueba..."
        python3 traffic_generator.py
        ;;
    *)
        echo "Operación no reconocida: ${OPERATION}"
        echo "Operaciones disponibles: load_json, scrape, server, generate_traffic"
        exit 1
        ;;
esac