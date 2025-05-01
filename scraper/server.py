# scraper/server.py
from flask import Flask, jsonify, request
import redis
import pymongo
import os
import json
from bson import ObjectId
import datetime

# Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DB_NAME = os.getenv("DB_NAME", "waze_data")
COLLECTION_NAME = "waze_events"

# Conexiones
app = Flask(__name__)
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Helper para transformar ObjectId y fechas a formato serializable
def serialize_doc(doc):
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    
    # Convertir fechas a formato ISO
    for key, value in doc.items():
        if isinstance(value, datetime.datetime):
            doc[key] = value.isoformat()
    
    return doc

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "endpoints": [
            "/api/events",
            "/api/event/<event_id>",
            "/api/random_ids",
            "/api/cache/stats",
            "/api/cache/clear"
        ]
    })

@app.route("/api/events", methods=["GET"])
def get_events():
    """Endpoint para obtener eventos con filtros opcionales"""
    # Parámetros de paginación
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 10)), 100)  # Limitar a máximo 100 registros
    skip = (page - 1) * limit
    
    # Filtros
    filters = {}
    for key in ["type", "subtype", "country", "city"]:
        if key in request.args:
            filters[key] = request.args.get(key)
    
    # Verificar si esta consulta está en caché
    cache_key = f"events:{json.dumps(filters)}:{page}:{limit}"
    cached = r.get(cache_key)
    
    if cached:
        return jsonify({
            "source": "cache",
            "page": page,
            "limit": limit,
            "events": json.loads(cached)
        })
    
    # Consultar MongoDB si no está en caché
    cursor = collection.find(filters).skip(skip).limit(limit)
    events = [serialize_doc(doc) for doc in cursor]
    
    # Guardar en caché (expira en 5 minutos)
    r.set(cache_key, json.dumps(events), ex=300)
    
    return jsonify({
        "source": "mongo",
        "page": page,
        "limit": limit,
        "events": events
    })

@app.route("/api/event/<string:event_id>", methods=["GET"])
def get_event(event_id):
    """Endpoint para obtener un evento específico por ID"""
    # Verificar si está en caché
    cached = r.get(f"event:{event_id}")
    if cached:
        return jsonify({
            "source": "cache",
            "event": json.loads(cached)
        })
    
    # Si no está en caché, consultarlo en MongoDB
    try:
        doc = collection.find_one({"_id": ObjectId(event_id)})
    except:
        return jsonify({"error": "ID de evento inválido"}), 400
    
    if doc:
        serialized_doc = serialize_doc(doc)
        # Guardar en caché (expira en 1 hora)
        r.set(f"event:{event_id}", json.dumps(serialized_doc), ex=3600)
        return jsonify({
            "source": "mongo",
            "event": serialized_doc
        })
    else:
        return jsonify({"error": "Evento no encontrado"}), 404

@app.route("/api/random_ids", methods=["GET"])
def get_random_ids():
    """Endpoint para obtener IDs aleatorios (útil para pruebas)"""
    n = min(int(request.args.get("n", 10)), 50)  # Limitar a máximo 50 IDs
    
    # Ejecutar una agregación para obtener documentos aleatorios
    random_docs = list(collection.aggregate([
        {"$sample": {"size": n}}
    ]))
    
    ids = [str(doc["_id"]) for doc in random_docs]
    return jsonify(ids)

@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Endpoint para ver estadísticas del cache"""
    try:
        # Obtener información sobre el uso de memoria
        info = r.info()
        
        # Obtener claves relacionadas con eventos
        event_keys = r.keys("event:*")
        events_list_keys = r.keys("events:*")
        
        # Obtener TTL para cada clave
        ttl_info = {}
        for key in event_keys + events_list_keys:
            ttl = r.ttl(key)
            ttl_info[key] = {
                "ttl_seconds": ttl,
                "ttl_human": f"{ttl//3600}h {(ttl%3600)//60}m {ttl%60}s" if ttl > 0 else "permanente"
            }
        
        cache_info = {
            "total_keys": len(r.keys("*")),
            "event_keys": len(event_keys),
            "events_list_keys": len(events_list_keys),
            "memory_used": info.get("used_memory_human", "N/A"),
            "memory_peak": info.get("used_memory_peak_human", "N/A"),
            "maxmemory": info.get("maxmemory_human", "N/A"),
            "maxmemory_policy": info.get("maxmemory_policy", "N/A"),
            "hit_rate": f"{info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100:.2f}%",
            "key_ttl_info": ttl_info
        }
        return jsonify(cache_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Endpoint para limpiar el cache"""
    try:
        # Borrar solo las claves relacionadas con eventos
        event_keys = r.keys("event:*")
        events_list_keys = r.keys("events:*")
        
        deleted = 0
        if event_keys:
            deleted += r.delete(*event_keys)
        if events_list_keys:
            deleted += r.delete(*events_list_keys)
            
        return jsonify({
            "message": "Cache limpiado correctamente",
            "keys_deleted": deleted
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)