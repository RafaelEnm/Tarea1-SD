import csv
import os
from pymongo import MongoClient

# Conexión a MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
db_name = os.getenv("DB_NAME", "waze_data")
collection_name = os.getenv("COLLECTION_NAME", "incidents")

# Ruta de salida
output_path = "/export/incidents.csv"

# Campos que deseas exportar
fields = ["_id", "type", "location", "timestamp", "description"]

client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

# Extraer datos
documents = collection.find({}, {field: 1 for field in fields})

# Escribir CSV
with open(output_path, mode="w", newline='', encoding="utf-8") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fields)
    writer.writeheader()
    for doc in documents:
        # Convertir ObjectId a str
        doc["_id"] = str(doc["_id"])
        writer.writerow({key: doc.get(key, "") for key in fields})

print(f"[✓] Exportación completada: {output_path}")
