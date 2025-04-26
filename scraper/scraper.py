import requests
import pymongo
import os
import folium
from datetime import datetime
import pandas as pd
import time
from pymongo.errors import ServerSelectionTimeoutError

# URL base de Waze para recolectar eventos
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"

# Límites de la Región Metropolitana
REGION_LIMITS = {
    "top": -33.079295,
    "bottom": -33.924396,
    "left": -71.371765,
    "right": -70.240173,
}

GRID_DIVISIONS = 6

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "waze_data")
COLLECTION_NAME = "waze_events"

def wait_for_mongo(uri, timeout=30):
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1000)
    start = time.time()
    while True:
        try:
            client.admin.command("ping")
            print("✅ Conexión a MongoDB establecida.")
            return
        except ServerSelectionTimeoutError:
            if time.time() - start > timeout:
                print("❌ Timeout al esperar MongoDB.")
                raise
            print("⏳ Esperando conexión a MongoDB...")
            time.sleep(1)

def connect_mongodb():
    """Crea una conexión a MongoDB."""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db

def divide_region(region_limits, divisions):
    lat_diff = (region_limits["top"] - region_limits["bottom"]) / divisions
    lon_diff = (region_limits["right"] - region_limits["left"]) / divisions

    grid = []
    for i in range(divisions):
        for j in range(divisions):
            square = {
                "top": region_limits["top"] - (i * lat_diff),
                "bottom": region_limits["top"] - ((i + 1) * lat_diff),
                "left": region_limits["left"] + (j * lon_diff),
                "right": region_limits["left"] + ((j + 1) * lon_diff),
            }
            grid.append(square)
    return grid

def fetch_waze_data(top, bottom, left, right):
    headers = {
        "User-Agent": "Mozilla/5.0"
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
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al realizar la petición a la API de Waze: {e}")
        return None

def process_waze_data(data):
    events = []
    if not data:
        print("No se encontraron datos en la respuesta de la API.")
        return events

    for alert in data.get('alerts', []):
        events.append({
            'type': 'Alert',
            **alert,
            'dateTime': datetime.fromtimestamp(alert.get('pubMillis', 0) / 1000.0).isoformat()
        })

    for jam in data.get('jams', []):
        events.append({
            'type': 'Jam',
            **jam,
            'dateTime': datetime.fromtimestamp(jam.get('pubMillis', 0) / 1000.0).isoformat()
        })

    return events

def save_to_mongodb(db, events):
    if not events:
        print("No hay eventos para guardar.")
        return
    collection = db[COLLECTION_NAME]
    for event in events:
        try:
            collection.insert_one(event)
        except Exception as e:
            print(f"Error al guardar el evento: {e}")

def visualize_data_from_db():
    client = pymongo.MongoClient(MONGO_URI)
    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        data = list(collection.find())

        if not data:
            print("No hay datos en la base de datos.")
            return

        df = pd.DataFrame(data)
        print(df.head(20))
    finally:
        client.close()

def main():
    wait_for_mongo(MONGO_URI)
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

    print(f"✅ Recolección completada. Total de eventos guardados: {total_events}")

if __name__ == "__main__":
    main()
