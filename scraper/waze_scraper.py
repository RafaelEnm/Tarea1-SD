import requests
import time
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
import os

def generate_santiago_parameters(index, total_divisions=32):
    # ... (esta función no necesita cambios)
    north_lat, south_lat = -33.20000, -33.70686
    west_lon, east_lon = -71.00000, -70.46603
    rows, columns = 4, 8
    cell_width = 0.0667
    cell_height = 0.1267
    row = index // columns
    column = index % columns
    top = north_lat - (row * cell_height)
    bottom = top - cell_height
    left = west_lon + (column * cell_width)
    right = left + cell_width
    return {
        "top": top, "bottom": bottom, "left": left, "right": right,
        "zone_name": f"Cell {index+1}", "cell_index": index,
        "total_cells": total_divisions, "row": row + 1, 
        "column": column + 1, "grid_size": f"{columns}x{rows}"
    }

def get_waze_data(coord_params):
    # ... (esta función no necesita cambios)
    url = "https://www.waze.com/live-map/api/georss"
    params = {
        'top': coord_params['top'], 'bottom': coord_params['bottom'],
        'left': coord_params['left'], 'right': coord_params['right'],
        'env': 'row', 'types': 'alerts,traffic,users'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"  -> Request error: {e}")
        return None

if __name__ == "__main__":
    print("=== WAZE DATA SCRAPER (ROBUST VERSION) ===")
    
    mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb://admin:admin123@mongo:27017/')
    mongodb_db = os.environ.get('MONGODB_DB', 'trafico_rm')
    
    try:
        client = MongoClient(mongodb_uri)
        db = client[mongodb_db]
        alerts_collection = db['alertas']
        jams_collection = db['atascos']
        alerts_collection.create_index([("uuid", 1)], unique=True, name='unique_alert_uuid')
        jams_collection.create_index([("uuid", 1)], unique=True, name='unique_jam_uuid')
        print("MongoDB connection and indexes OK.")
    except Exception as e:
        print(f"FATAL: Could not connect to MongoDB. Error: {e}")
        exit(1)
    
    total_cells = 32
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_alerts_found = total_jams_found = 0
    total_alerts_upserted = total_jams_upserted = 0
    
    print(f"\nQuerying {total_cells} cells...")
    
    for i in range(total_cells):
        print(f"\nQuerying cell {i+1}/{total_cells}...")
        coords = generate_santiago_parameters(i)
        data = get_waze_data(coords)
        
        if not data:
            print("  -> No data received from Waze API.")
            continue
            
        # --- CAMBIO CLAVE 1: Procesar con "upsert" (UPDATE + INSERT) ---
        # Process alerts
        if data.get('alerts'):
            operations = []
            for alert in data['alerts']:
                alert['last_updated'] = current_date
                # Prepara una operación de "actualizar o insertar"
                operations.append(
                    UpdateOne({'uuid': alert['uuid']}, {'$set': alert}, upsert=True)
                )
            
            alerts_in_batch = len(operations)
            total_alerts_found += alerts_in_batch
            print(f"  -> Found {alerts_in_batch} alerts.")

            if operations:
                try:
                    result = alerts_collection.bulk_write(operations, ordered=False)
                    total_alerts_upserted += result.upserted_count + result.modified_count
                except BulkWriteError as bwe:
                    # Imprime un error útil en lugar de fallar silenciosamente
                    print(f"  -> WARNING: Bulk write error for alerts. Details: {bwe.details}")

        # Process jams
        if data.get('jams'):
            operations = []
            for jam in data['jams']:
                jam['last_updated'] = current_date
                operations.append(
                    UpdateOne({'uuid': jam['uuid']}, {'$set': jam}, upsert=True)
                )

            jams_in_batch = len(operations)
            total_jams_found += jams_in_batch
            print(f"  -> Found {jams_in_batch} jams.")

            if operations:
                try:
                    result = jams_collection.bulk_write(operations, ordered=False)
                    total_jams_upserted += result.upserted_count + result.modified_count
                except BulkWriteError as bwe:
                    print(f"  -> WARNING: Bulk write error for jams. Details: {bwe.details}")
        
        if i < total_cells - 1:
            time.sleep(2)
    
    print("\n=== SCRAPING COMPLETED ===")
    print(f"Total alerts found: {total_alerts_found} | Total alerts upserted/modified: {total_alerts_upserted}")
    print(f"Total jams found: {total_jams_found} | Total jams upserted/modified: {total_jams_upserted}")