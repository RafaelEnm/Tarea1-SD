#!/usr/bin/env python3
import os
import csv
import pymongo
from datetime import datetime
import json

def process_city(city):
    """Procesa el campo ciudad para formatear y reemplazar comas por punto y coma"""
    if city and isinstance(city, str):
        city = city.replace(',', ';')
        city_parts = city.split(';')
        city_parts = [part.strip().title() for part in city_parts]
        return ';'.join(city_parts)
    return city

def main():
    print("🔄 Iniciando exportación desde MongoDB...")
    
    # Configuración desde variables de entorno
    mongo_uri = os.environ.get('MONGODB_URI')
    mongo_db = os.environ.get('MONGODB_DB')
    
    # Usar nombres por defecto si no están definidos
    alertas_collection = os.environ.get('MONGODB_COLECCION_ALERTAS', 'alertas')
    atascos_collection = os.environ.get('MONGODB_COLECCION_ATASCOS', 'atascos')
    
    # Conectar a MongoDB
    client = pymongo.MongoClient(mongo_uri)
    db = client[mongo_db]
    
    # Timestamp para archivos únicos y para el nombre de la carpeta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # =========================================================================
    # ===================> CAMBIO CLAVE REALIZADO AQUÍ <===================
    # =========================================================================
    # El directorio de salida debe ser /app/data para que data_filter.pig lo encuentre.
    output_dir = "/app/data"
    # =========================================================================
    # ======================= FIN DEL CAMBIO CLAVE ========================
    # =========================================================================
    
    # Crear directorio base
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear directorio específico para esta ejecución
    execution_dir = os.path.join(output_dir, f"execution_{timestamp}")
    os.makedirs(execution_dir, exist_ok=True)
    
    print(f"📁 Directorio de salida: {execution_dir}")
    
    # Exportar alertas
    alertas_file = os.path.join(execution_dir, f"transformed_alerta_{timestamp}.csv")
    alert_fields = [
        "uuid", "city", "municipalityUser", "type", 
        "street", "confidence", "location_x", "location_y", "fecha"
    ]
    
    with open(alertas_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, fieldnames=alert_fields, 
            delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
            extrasaction='ignore' # Ignorar campos extra que no están en la lista
        )
        writer.writeheader()
        alertas_count = 0
        
        for doc in db[alertas_collection].find({}, {'_id': 0}):
            row = {
                "uuid": doc.get("uuid"),
                "city": process_city(doc.get("city")),
                "municipalityUser": doc.get("reportByMunicipalityUser", doc.get("municipalityUser")),
                "type": doc.get("type"),
                "street": doc.get("street"),
                "confidence": doc.get("confidence"),
                "location_x": doc.get("location", {}).get("x"),
                "location_y": doc.get("location", {}).get("y"),
                "fecha": doc.get("pubMillis") # Usar pubMillis si existe, si no, el campo fecha
            }
            # Unificar el campo de fecha, ya que los datos de Waze usan pubMillis
            if 'pubMillis' in doc:
                row['fecha'] = datetime.fromtimestamp(doc['pubMillis'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                row['fecha'] = doc.get('fecha', '')
                
            writer.writerow(row)
            alertas_count += 1
    
    print(f"✅ Exportadas {alertas_count} alertas")
    
    # Exportar atascos
    atascos_file = os.path.join(execution_dir, f"transformed_atasco_{timestamp}.csv")
    jam_fields = [
        "uuid", "severity", "country", "length", "endnode", "roadtype", 
        "speed", "street", "fecha", "region", "city"
    ]
    
    with open(atascos_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, fieldnames=jam_fields, 
            delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL,
            extrasaction='ignore'
        )
        writer.writeheader()
        atascos_count = 0
        
        for doc in db[atascos_collection].find({}, {'_id': 0}):
            row = {
                "uuid": doc.get("uuid"),
                "severity": doc.get("severity"),
                "country": doc.get("country"),
                "length": doc.get("length"),
                "endnode": doc.get("endNode"),
                "roadtype": doc.get("roadType"),
                "speed": doc.get("speedKMH", doc.get("speed")),
                "street": doc.get("street"),
                "region": doc.get("region"),
                "city": process_city(doc.get("city"))
            }
            if 'pubMillis' in doc:
                row['fecha'] = datetime.fromtimestamp(doc['pubMillis'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                row['fecha'] = doc.get('fecha', '')

            writer.writerow(row)
            atascos_count += 1
    
    print(f"✅ Exportados {atascos_count} atascos")
    print(f"🎯 Exportación completada en: {execution_dir}")
    
    # Crear archivo de resumen
    summary = {
        "timestamp": timestamp,
        "execution_dir": execution_dir,
        "alerts_exported": alertas_count,
        "jams_exported": atascos_count,
        "alerts_file": alertas_file,
        "jams_file": atascos_file
    }
    
    with open(os.path.join(execution_dir, "export_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Resumen guardado en: {execution_dir}/export_summary.json")

if __name__ == "__main__":
    main()