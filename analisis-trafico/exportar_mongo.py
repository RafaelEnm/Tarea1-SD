#!/usr/bin/env python3
import os
import csv
import pymongo
from datetime import datetime

def procesar_ciudad(city):
    if not city or not isinstance(city, str):
        return city
    
    # Reemplazar comas por punto y coma
    city_limpia = city.replace(',', ';')
    partes = city_limpia.split(';')
    partes_formateadas = [parte.strip().title() for parte in partes]
    
    return ';'.join(partes_formateadas)

def main():
    print("Iniciando exportación desde MongoDB")
    
    # Variables de configuración
    mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://mongo:27017/')
    mongo_db = os.environ.get('MONGODB_DB', 'waze_data')
    col_alertas = os.environ.get('MONGODB_COLECCION_ALERTAS', 'alertas')
    col_atascos = os.environ.get('MONGODB_COLECCION_ATASCOS', 'atascos')
    
    # Conexión a la base de datos
    client = pymongo.MongoClient(mongo_uri)
    database = client[mongo_db]
    
    # Crear directorio y timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    directorio_salida = "/app/data"
    os.makedirs(directorio_salida, exist_ok=True)
    
    # Procesar alertas
    archivo_alertas = f"{directorio_salida}/transformed_alerta_alertas_{timestamp}.csv"
    columnas_alertas = [
        "uuid", "city", "municipalityUser", "type", "street", 
        "confidence", "location_x", "location_y", "fecha"
    ]
    
    with open(archivo_alertas, 'w', newline='') as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=columnas_alertas, delimiter=',', 
            quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        escritor.writeheader()
        
        contador_alertas = 0
        for documento in database[col_alertas].find({}, {'_id': 0}):
            ciudad_procesada = procesar_ciudad(documento.get("city", ""))
            registro = {
                "uuid": documento.get("uuid", f"item_{contador_alertas}"),
                "city": ciudad_procesada,
                "municipalityUser": documento.get("reportByMunicipalityUser", ""),
                "type": documento.get("type", ""),
                "street": documento.get("street", ""),
                "confidence": documento.get("confidence", 0),
                "location_x": documento.get("location", {}).get("x", documento.get("x", 0)),
                "location_y": documento.get("location", {}).get("y", documento.get("y", 0)),
                "fecha": documento.get("fecha", "")
            }
            escritor.writerow(registro)
            contador_alertas += 1
    
    print(f"Exportadas {contador_alertas} alertas")
    
    # Procesar atascos
    archivo_atascos = f"{directorio_salida}/transformed_atasco_atascos_{timestamp}.csv"
    columnas_atascos = [
        "uuid", "severity", "country", "length", "endnode", 
        "roadtype", "speed", "street", "fecha", "region", "city"
    ]
    
    with open(archivo_atascos, 'w', newline='') as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=columnas_atascos, delimiter=',', 
            quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        escritor.writeheader()
        
        contador_atascos = 0
        for documento in database[col_atascos].find({}, {'_id': 0}):
            ciudad_procesada = procesar_ciudad(documento.get("city", ""))
            registro = {
                "uuid": documento.get("uuid", f"item_{contador_atascos}"),
                "severity": documento.get("severity", ""),
                "country": documento.get("country", ""),
                "length": documento.get("length", ""),
                "endnode": documento.get("endNode", ""),
                "roadtype": documento.get("roadType", ""),
                "speed": documento.get("speedKMH", documento.get("speed", "")),
                "street": documento.get("street", ""),
                "fecha": documento.get("fecha", ""),
                "region": documento.get("region", ""),
                "city": ciudad_procesada
            }
            escritor.writerow(registro)
            contador_atascos += 1
    
    print(f"Exportados {contador_atascos} atascos")
    print("Exportación completada")

if __name__ == "__main__":
    main()