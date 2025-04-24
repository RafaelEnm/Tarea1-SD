import requests
import pymongo
import os
import folium
from datetime import datetime
import pandas as pd  # Para visualizar los datos en forma de tabla

# URL base de Waze para recolectar eventos
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"

# Límites de la Región Metropolitana
REGION_LIMITS = {
    "top": -33.079295,  # Coordenada latitud superior
    "bottom": -33.924396,  # Coordenada latitud inferior
    "left": -71.371765,  # Coordenada longitud izquierda
    "right": -70.240173,  # Coordenada longitud derecha
}

# Número de divisiones en la cuadrícula
GRID_DIVISIONS = 6

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "waze_data")
COLLECTION_NAME = "waze_events"

def connect_mongodb():
    """Crea una conexión a MongoDB."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db

def divide_region(region_limits, divisions):
    """Divide la región en una cuadrícula."""
    lat_diff = (region_limits["top"] - region_limits["bottom"]) / divisions
    lon_diff = (region_limits["right"] - region_limits["left"]) / divisions

    grid = []
    for i in range(divisions):
        for j in range(divisions):
            # Calcula los límites de cada cuadrado
            square = {
                "top": region_limits["top"] - (i * lat_diff),
                "bottom": region_limits["top"] - ((i + 1) * lat_diff),
                "left": region_limits["left"] + (j * lon_diff),
                "right": region_limits["left"] + ((j + 1) * lon_diff),
            }
            grid.append(square)
    return grid

def fetch_waze_data(top, bottom, left, right):
    """Obtiene datos desde la API de Waze para un área específica."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "env": "row",
        "types": "alerts,traffic,users",
    }
    try:
        response = requests.get(WAZE_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Verifica si la solicitud fue exitosa
        return response.json()
    except requests.RequestException as e:
        print(f"Error al realizar la petición a la API de Waze: {e}")
        return None

def process_waze_data(data):
    """Procesa los datos obtenidos de la API de Waze."""
    events = []
    if not data:
        print("No se encontraron datos en la respuesta de la API.")
        return events

    # Procesar los "alerts"
    for alert in data.get('alerts', []):
        events.append({
            'type': 'Alert',
            **alert,  # Incluye todos los campos del objeto "alert"
            'dateTime': datetime.fromtimestamp(alert.get('pubMillis', 0) / 1000.0).isoformat()  # Convierte el timestamp a ISO 8601
        })

    # Procesar los "jams"
    for jam in data.get('jams', []):
        events.append({
            'type': 'Jam',
            **jam,  # Incluye todos los campos del objeto "jam"
            'dateTime': datetime.fromtimestamp(jam.get('pubMillis', 0) / 1000.0).isoformat()  # Convierte el timestamp a ISO 8601
        })

    return events

def save_to_mongodb(db, events):
    """Guarda los eventos en MongoDB, incluyendo duplicados y eventos con valores nulos."""
    if not events:
        print("No hay eventos para guardar.")
        return
    collection = db[COLLECTION_NAME]
    for event in events:
        try:
            # Inserta cada evento sin filtrar duplicados ni validar campos
            collection.insert_one(event)
        except Exception as e:
            print(f"Error al guardar el evento: {e}")

def visualize_data_from_db():
    """Visualiza los datos de la base de datos en forma de tabla."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Obtiene todos los documentos de la colección
    data = list(collection.find())

    if not data:
        print("No hay datos en la base de datos.")
        return

    # Convierte los datos a un DataFrame de pandas
    df = pd.DataFrame(data)

    # Muestra los datos en forma de tabla
    print(df.head(20))  # Muestra las primeras 20 filas

def main():
    db = connect_mongodb()
    grid = divide_region(REGION_LIMITS, GRID_DIVISIONS)



    total_events = 0
    for square in grid:
        print(f"Recolectando datos para el área: {square}")
        data = fetch_waze_data(
            top=square["top"],
            bottom=square["bottom"],
            left=square["left"],
            right=square["right"]
        )
        if data:
            events = process_waze_data(data)
            save_to_mongodb(db, events)
            total_events += len(events)

    print(f"Recolección completada. Total de eventos guardados: {total_events}")

if __name__ == "__main__":
    main()