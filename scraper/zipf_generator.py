import json
from scipy.stats import zipf, expon
import numpy as np
import requests
import time
from datetime import datetime

# Configuración rápida para pruebas
api_base_url = "http://api_server:5000"
total_samples = 1000  # Reducir para pruebas rápidas (original: 100000)
a_zipf = 1.3  # Parámetro Zipf (mayor = más sesgo)
lambda_exp = 0.5  # Parámetro exponencial (menor = más rápido)

# Obtener UUIDs (tu código original)
combined_uuids = []

try:
    alertas = requests.get(f"{api_base_url}/uuids_alertas").json()
    combined_uuids.extend([{"tipo": "alerta", "uuid": uuid} for uuid in alertas])
    print(f"Se obtuvieron {len(alertas)} UUIDs de alertas")
except Exception as e:
    print(f"Error al obtener alertas: {e}")
    alertas = []

try:
    atascos = requests.get(f"{api_base_url}/uuids_atascos").json()
    combined_uuids.extend([{"tipo": "atasco", "uuid": uuid} for uuid in atascos])
    print(f"Se obtuvieron {len(atascos)} UUIDs de atascos")
except Exception as e:
    print(f"Error al obtener atascos: {e}")
    atascos = []

if not combined_uuids:
    print("No hay UUIDs. Verificar API.")
    exit(1)

# Generar distribución Zipf de consultas
n = len(combined_uuids)
zipf_indices = zipf.rvs(a=a_zipf, size=total_samples) - 1
zipf_indices = zipf_indices % n
zipf_uuids = [combined_uuids[int(idx)] for idx in zipf_indices]

# Generar tiempos entre consultas (distribución exponencial rápida)
tiempos_entre_consultas = expon.rvs(scale=1/lambda_exp, size=total_samples)

# Guardar distribución ZipF generada
with open("/app/data/zipf_distribution_uuids.json", 'w') as f:
    json.dump(zipf_uuids, f)

print(f"Se guardaron {len(zipf_uuids)} UUIDs con distribución ZipF en /app/data/zipf_distribution_uuids.json")

total_requests = cache_hits = cache_misses = not_found = 0
start_time = datetime.now()

for i, item in enumerate(zipf_uuids):
    tipo, uuid = item["tipo"], item["uuid"]
    url = f"{api_base_url}/{tipo}/{uuid}"
    
    if i > 0:  
        time.sleep(tiempos_entre_consultas[i])
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('resultado') == 'hit':
            cache_hits += 1
        elif data.get('resultado') == 'miss':
            cache_misses += 1
        elif data.get('resultado') == 'no_encontrado':
            not_found += 1
        total_requests += 1
    
    except Exception as e:
        print(f"Error en {url}: {e}")

# Resultados
hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
total_time = (datetime.now() - start_time).total_seconds()

print("\n--- Resultados ZipF ---")
print(f"Total consultas: {total_requests}")
print(f"Cache hits: {cache_hits} ({hit_rate:.2f}%)")
print(f"Cache misses: {cache_misses}")
print(f"No encontrados: {not_found}")
print(f"Tiempo total: {total_time:.2f} segundos")
print(f"Consultas/segundo: {total_requests / total_time:.2f}")

# Guardar resultados
results = {
    "distribution_type": "zipf",
    "total_requests": total_requests,
    "cache_hits": cache_hits,
    "cache_misses": cache_misses,
    "not_found": not_found,
    "hit_rate": hit_rate,
    "total_time_seconds": total_time,
    "requests_per_second": total_requests / total_time if total_time > 0 else 0,
    "zipf_parameter": a_zipf,
    "exponential_parameter": lambda_exp
}

with open("/app/data/zipf_traffic_results.json", "w") as f:
    json.dump(results, f)

print(f"Resultados guardados en /app/data/zipf_traffic_results.json")