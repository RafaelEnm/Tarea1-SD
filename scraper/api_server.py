from flask import Flask, request, jsonify
import redis
import pymongo
import json
import os
from bson import json_util
import time

app = Flask(__name__)

# Conexión a Redis
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=0
)

# Conexión a MongoDB
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
mongo_client = pymongo.MongoClient(mongo_uri)
mongo_db = mongo_client[os.environ.get('MONGO_DB', 'trafico_rm')]
alertas_collection = mongo_db['alertas']
atascos_collection = mongo_db['atascos']

# Tiempo de expiración de caché en Redis (en segundos)
CACHE_EXPIRATION = 300  # 5 minutos, frescura para tiempo real

@app.route('/', methods=['GET'])
def index():
    return '''
        <h1>Bienvenido a la API de tráfico</h1>
        <p>Sistema de análisis de tráfico distribuido</p>
    '''

# Rutas para obtener todos los UUIDs de alertas y atascos
@app.route('/uuids_alertas', methods=['GET'])
def get_uuids_alertas():
    try:
        uuids = list(alertas_collection.find({}, {"uuid": 1, "_id": 0}))
        uuid_list = [doc.get('uuid') for doc in uuids if doc.get('uuid')]
        return jsonify(uuid_list)
    
    except Exception as e:
        app.logger.error(f"Error retrieving alertas UUIDs: {str(e)}")
        return jsonify({'error': f'Error retrieving alertas UUIDs: {str(e)}'}), 500

@app.route('/uuids_atascos', methods=['GET'])
def get_uuids_atascos():
    print("Entrando a la ruta /uuids_atascos")
    app.logger.info("Entrando a la ruta /uuids_atascos")
    try:
        # Verificar conexión
        server_info = mongo_client.server_info()
        app.logger.info(f"Conexión a MongoDB exitosa: versión {server_info.get('version', 'desconocida')}")
        
        # Contar documentos antes de la consulta
        total_docs = atascos_collection.count_documents({})
        app.logger.info(f"Total de documentos en la colección atascos: {total_docs}")
        
        # Proyección para obtener solo los UUIDs de los atascos
        uuids = list(atascos_collection.find({}, {"uuid": 1, "_id": 0}))
        app.logger.info(f"Documentos recuperados en la proyección: {len(uuids)}")
        
        # Diagnóstico: Inspeccionar documentos recuperados
        for i, doc in enumerate(uuids[:5]):  # Solo los primeros 5 para no saturar logs
            app.logger.info(f"Documento {i}: {doc}")
        
        # Extraer solo los valores de UUID en una lista simple
        uuid_list = [doc.get('uuid') for doc in uuids if doc.get('uuid')]
        
        app.logger.info(f"UUIDs extraídos: {len(uuid_list)}")
        if uuid_list:
            app.logger.info(f"Primeros UUIDs: {uuid_list[:5]}")
        else:
            app.logger.warning("No se encontraron UUIDs en los documentos")
        
        return jsonify(uuid_list)
        
    except pymongo.errors.ConnectionFailure as e:
        app.logger.error(f"Error de conexión a MongoDB: {str(e)}")
        return jsonify({'error': f'Error de conexión a MongoDB: {str(e)}'}), 500
        
    except Exception as e:
        app.logger.error(f"Error retrieving atascos UUIDs: {str(e)}")
        return jsonify({'error': f'Error retrieving atascos UUIDs: {str(e)}'}), 500

# Rutas para que el generador de tráfico pregunte por alertas y atascos
@app.route('/alerta/<uuid>', methods=['GET'])
def get_alerta(uuid):
    # Buscar en Redis primero
    cache_key = f"alerta:{uuid}"
    inicio_tiempo_cache = time.time()
    cached_data = redis_client.get(cache_key)
    fin_tiempo_cache = time.time()
    tiempo_cache = fin_tiempo_cache - inicio_tiempo_cache
    tiempo_cache_ms = round(tiempo_cache * 1000, 2)  # Convertir a milisegundos
    
    if cached_data:
        # Si el registro está en caché
        app.logger.info(f"Cache hit for alerta UUID: {uuid}")
        return jsonify({"resultado": "hit", "tiempo (ms)": tiempo_cache_ms})
    
    # Si no está en Redis, buscar en MongoDB
    app.logger.info(f"Cache miss for alerta UUID: {uuid}, querying MongoDB")

    inicio_tiempo_mongo = time.time()
    alerta = alertas_collection.find_one({"uuid": uuid})
    fin_tiempo_mongo = time.time()
    tiempo_mongo = fin_tiempo_mongo - inicio_tiempo_mongo
    tiempo_mongo_ms = round(tiempo_mongo * 1000, 2)  # Convertir a milisegundos
    
    if not alerta:
        return jsonify({"resultado": "no_encontrado"})
    
    # Convertir el documento BSON a JSON
    alerta_json = json.loads(json_util.dumps(alerta))
    
    # Guardar en Redis para futuras consultas
    redis_client.setex(
        cache_key,
        CACHE_EXPIRATION,
        json.dumps(alerta_json)
    )
    
    return jsonify({"resultado": "miss", "tiempo (ms)": tiempo_mongo_ms})

@app.route('/atasco/<uuid>', methods=['GET'])
def get_atasco(uuid):
    # Buscar en Redis primero
    cache_key = f"atasco:{uuid}"
    inicio_tiempo_cache = time.time()
    cached_data = redis_client.get(cache_key)
    fin_tiempo_cache = time.time()
    tiempo_cache = fin_tiempo_cache - inicio_tiempo_cache
    tiempo_cache_ms = round(tiempo_cache * 1000, 2)  # Convertir a milisegundos
    
    if cached_data:
        # Si el registro está en caché
        app.logger.info(f"Cache hit for atasco UUID: {uuid}")
        return jsonify({"resultado": "hit", "tiempo (ms)": tiempo_cache_ms})
    
    # Si no está en Redis, buscar en MongoDB
    app.logger.info(f"Cache miss for atasco UUID: {uuid}, querying MongoDB")
    
    atasco = None

    # Si parece ser un número, intentar con formato numérico
    if uuid.isdigit():
        inicio_tiempo_mongo = time.time()
        atasco = atascos_collection.find_one({"uuid": int(uuid)})  # Se convierte a int porque los uuids de atasco son int
        fin_tiempo_mongo = time.time()
        tiempo_mongo = fin_tiempo_mongo - inicio_tiempo_mongo
        tiempo_mongo_ms = round(tiempo_mongo * 1000, 2)  # Convertir a milisegundos
    
    # Si sigue sin encontrarse
    if not atasco:
        return jsonify({"resultado": "no_encontrado"})
    
    # Convertir el documento BSON a JSON
    atasco_json = json.loads(json_util.dumps(atasco))
    
    # Guardar en Redis para futuras consultas
    redis_client.setex(
        cache_key,
        CACHE_EXPIRATION,
        json.dumps(atasco_json)
    )
    
    return jsonify({"resultado": "miss", "tiempo (ms)": tiempo_mongo_ms})

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"Error: {str(e)}")
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))