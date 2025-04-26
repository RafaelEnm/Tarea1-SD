import redis
import pymongo
import random
import time
import os
import json
import numpy as np
from bson import ObjectId
from datetime import datetime
from collections import OrderedDict, Counter

# Configuración
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = "waze_data"
COLLECTION_NAME = "waze_events"
TOTAL_QUERIES = 1000
CACHE_SIZE = 200  # Tamaño máximo del caché

# Distribuciones de tráfico disponibles
TRAFFIC_DISTRIBUTIONS = ["uniform", "zipf"]

# Políticas de caché disponibles
CACHE_POLICIES = ["simple", "lru", "lfu"]

# Conexiones
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Obtener 500 _id aleatorios de Mongo
ids = [str(doc["_id"]) for doc in collection.aggregate([{ "$sample": { "size": 500 } }])]
print(f"➡️ Obtenidos {len(ids)} IDs únicos para simulación\n")

# Función para distribución Zipf (favorece algunos IDs sobre otros)
def zipf_distribution(ids, alpha=1.5):
    weights = np.array([1/(i+1)**alpha for i in range(len(ids))])
    weights = weights / weights.sum()
    return lambda: np.random.choice(ids, p=weights)

# Función para distribución uniforme
def uniform_distribution(ids):
    return lambda: random.choice(ids)

# Clase base para políticas de caché
class CachePolicy:
    def __init__(self, redis_client, max_size=CACHE_SIZE, ttl=3600):
        self.redis = redis_client
        self.max_size = max_size
        self.ttl = ttl
        
    def get(self, key):
        return self.redis.get(key)
        
    def set(self, key, value):
        if self.redis.dbsize() >= self.max_size:
            self.evict()
        self.redis.set(key, value, ex=self.ttl)
        
    def evict(self):
        # Implementado por subclases
        pass

# Política simple: usa expiración automática de Redis
class SimpleCache(CachePolicy):
    def evict(self):
        # No hace nada, confía en la expiración automática
        pass

# Política LRU (Least Recently Used)
class LRUCache(CachePolicy):
    def __init__(self, redis_client, max_size=CACHE_SIZE, ttl=3600):
        super().__init__(redis_client, max_size, ttl)
        self.usage_tracker = OrderedDict()
        
    def get(self, key):
        value = super().get(key)
        if value:
            # Actualizar el uso (mover al final)
            if key in self.usage_tracker:
                del self.usage_tracker[key]
            self.usage_tracker[key] = time.time()
        return value
        
    def set(self, key, value):
        super().set(key, value)
        self.usage_tracker[key] = time.time()
        
    def evict(self):
        # Eliminar el elemento menos recientemente usado
        if self.usage_tracker:
            oldest_key, _ = next(iter(self.usage_tracker.items()))
            self.redis.delete(oldest_key)
            del self.usage_tracker[oldest_key]

# Política LFU (Least Frequently Used)
class LFUCache(CachePolicy):
    def __init__(self, redis_client, max_size=CACHE_SIZE, ttl=3600):
        super().__init__(redis_client, max_size, ttl)
        self.frequency = Counter()
        
    def get(self, key):
        value = super().get(key)
        if value:
            self.frequency[key] += 1
        return value
        
    def set(self, key, value):
        super().set(key, value)
        self.frequency[key] = 1
        
    def evict(self):
        # Eliminar el elemento menos frecuentemente usado
        if self.frequency:
            least_common = self.frequency.most_common()[:-2:-1]
            if least_common:
                key_to_evict = least_common[0][0]
                self.redis.delete(key_to_evict)
                del self.frequency[key_to_evict]

# Función para ejecutar una simulación con parámetros específicos
def run_simulation(distribution_type, cache_policy_type):
    # Inicializar distribución
    if distribution_type == "uniform":
        next_query = uniform_distribution(ids)
    else:  # zipf
        next_query = zipf_distribution(ids)
    
    # Inicializar política de caché
    if cache_policy_type == "simple":
        cache = SimpleCache(r)
    elif cache_policy_type == "lru":
        cache = LRUCache(r)
    else:  # lfu
        cache = LFUCache(r)
    
    # Limpiar caché antes de empezar
    r.flushall()
    
    # Métricas
    hits = 0
    misses = 0
    latencies = []
    
    print(f"🚀 Iniciando simulación con distribución {distribution_type} y política {cache_policy_type}")
    
    # Ejecutar consultas
    for i in range(TOTAL_QUERIES):
        eid = next_query()
        start_time = time.time()
        
        # Intentar obtener de caché
        cached = cache.get(eid)
        
        if cached:
            # Hit de caché
            hits += 1
            print(f"[{i}] HIT ✅  -> {eid}")
        else:
            # Miss de caché
            misses += 1
            print(f"[{i}] MISS ❌ -> {eid}")
            
            # Obtener de MongoDB
            event = collection.find_one({"_id": ObjectId(eid)})
            if event:
                event["_id"] = str(event["_id"])
                cache.set(eid, str(event))
        
        # Medir latencia
        latency = time.time() - start_time
        latencies.append(latency)
        
        time.sleep(0.01)  # Simular tiempo entre consultas
    
    # Calcular métricas finales
    hit_rate = hits / TOTAL_QUERIES if TOTAL_QUERIES > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    # Resultados
    results = {
        "distribution": distribution_type,
        "cache_policy": cache_policy_type,
        "cache_size": CACHE_SIZE,
        "total_queries": TOTAL_QUERIES,
        "hits": hits,
        "misses": misses,
        "hit_rate": hit_rate,
        "avg_latency": avg_latency,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n📊 Resultados:")
    print(f"   Hit rate: {hit_rate:.2%}")
    print(f"   Latencia promedio: {avg_latency*1000:.2f} ms\n")
    
    # Guardar resultados
    with open(f"results_{distribution_type}_{cache_policy_type}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

# Ejecutar todas las combinaciones de simulaciones
all_results = []

for dist in TRAFFIC_DISTRIBUTIONS:
    for policy in CACHE_POLICIES:
        result = run_simulation(dist, policy)
        all_results.append(result)
        time.sleep(1)  # Pausa entre simulaciones

# Guardar todos los resultados juntos
with open("all_simulation_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("✅ Todas las simulaciones completadas!")