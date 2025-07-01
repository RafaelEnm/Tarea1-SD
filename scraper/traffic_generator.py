import json
from scipy.stats import norm
import numpy as np
import requests
import time

# Definir la URL base de la API
api_base_url = "http://api_server:5000"  # Usando el nombre del servicio como hostname

# Lista para almacenar todos los UUIDs con su tipo
combined_uuids = []

# Obtener UUIDs de alertas desde la API
try:
    alertas_response = requests.get(f"{api_base_url}/uuids_alertas")
    alertas_response.raise_for_status()  # Lanzar excepción si hay error HTTP
    alertas = alertas_response.json()
    
    for uuid in alertas:
        combined_uuids.append({"tipo": "alerta", "uuid": uuid})
    
    print(f"Se obtuvieron {len(alertas)} UUIDs de alertas desde la API")
except requests.exceptions.RequestException as e:
    print(f"Error al obtener UUIDs de alertas desde la API: {e}")
    alertas = []

# Obtener UUIDs de atascos desde la API
try:
    atascos_response = requests.get(f"{api_base_url}/uuids_atascos")
    atascos_response.raise_for_status()  # Lanzar excepción si hay error HTTP
    atascos = atascos_response.json()
    
    for uuid in atascos:
        combined_uuids.append({"tipo": "atasco", "uuid": uuid})
    
    print(f"Se obtuvieron {len(atascos)} UUIDs de atascos desde la API")
except requests.exceptions.RequestException as e:
    print(f"Error al obtener UUIDs de atascos desde la API: {e}")
    atascos = []

print(f"Se encontraron {len(combined_uuids)} UUIDs únicos en total")

# Si no se obtuvieron UUIDs, terminar
if not combined_uuids:
    print("No se obtuvieron UUIDs. Verificar la conexión con la API o si hay datos disponibles.")
    exit(1)

# Generar distribución Normal
total_samples = 50000  # Cantidad de elementos en la distribución final
n = len(combined_uuids)

# Configurar la distribución normal
mu = n / 2  # Media en el centro de la lista
sigma = n / 3  # Ajustamos la desviación estándar para mejor distribución

print(f"Usando: mu={mu}, sigma={sigma}")

# Mezclar aleatoriamente los UUIDs para evitar sesgos por orden inicial
np.random.shuffle(combined_uuids)

# Usar scipy.stats.norm para crear la distribución
distribution = norm(loc=mu, scale=sigma)
# Generar valores aleatorios siguiendo la distribución
normal_values = distribution.rvs(size=total_samples)
# Redondear y limitar a los índices válidos
normal_indices = np.clip(np.round(normal_values).astype(int), 0, n-1)

# Crear una lista con la distribución normal
normal_uuids = [combined_uuids[idx] for idx in normal_indices]

# Guardar la distribución normal como JSON
with open("/app/data/normal_distribution_uuids.json", 'w') as f:
    json.dump(normal_uuids, f)

print(f"Se guardaron {len(normal_uuids)} UUIDs con distribución Normal en /app/data/normal_distribution_uuids.json")

# También guardar la lista original de UUIDs únicos
with open("/app/data/unique_uuids.json", 'w') as f:
    json.dump(combined_uuids, f)

print(f"Se guardaron {len(combined_uuids)} UUIDs únicos en /app/data/unique_uuids.json")

# Consultar la API para cada UUID en la distribución Normal
print("\nConsultando la API para cada UUID en la distribución Normal...")

# Contadores para estadísticas
total_requests = 0
cache_hits = 0
cache_misses = 0
not_found = 0
tiempos_cache = []
tiempos_no_cache = []
# Iniciar conteo de tiempo
start_time = time.time()
tiempo_cache = 0.000
tiempo_no_cache = 0.000

# Realizar las consultas a la API
for item in normal_uuids:
    tipo = item["tipo"]
    uuid = item["uuid"]
    
    # Construir la URL según el tipo
    if tipo == "alerta":
        url = f"{api_base_url}/alerta/{uuid}"
    elif tipo == "atasco":
        url = f"{api_base_url}/atasco/{uuid}"
    else:
        print(f"Tipo desconocido: {tipo}")
        continue
    
    total_requests += 1
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanzar excepción si hay error HTTP
        
        # Analizar la respuesta para determinar si fue hit, miss o no_encontrado
        data = response.json()
        
        if data.get('resultado') == 'hit':
            cache_hits += 1
            tiempos_cache.append(float(data.get('tiempo (ms)')))
            tiempo_cache += float(data.get('tiempo (ms)'))
        elif data.get('resultado') == 'miss':
            cache_misses += 1
            tiempos_no_cache.append(float(data.get('tiempo (ms)')))
            tiempo_no_cache += float(data.get('tiempo (ms)'))
        elif data.get('resultado') == 'no_encontrado':
            not_found += 1
        
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {tipo} con UUID {uuid}: {e}")

# Calcular tiempo total de todas las consultas
end_time = time.time()
total_time = end_time - start_time

# Calcular el hit rate
hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0

# Calcular el tiempo promedio por consulta cache y no cache
tiempo_promedio_cache = tiempo_cache / cache_hits if cache_hits > 0 else 0
tiempo_promedio_no_cache = tiempo_no_cache / cache_misses if cache_misses > 0 else 0

# Mostrar estadísticas
print("\nResultados de las consultas:")
print(f"Total de consultas: {total_requests}")
print(f"Cache hits: {cache_hits}")
print(f"Cache misses: {cache_misses}")
print(f"No encontrados: {not_found}")
print(f"Hit rate: {hit_rate:.2f}%")
print(f"Tiempo total: {total_time:.2f} segundos")

# Guardar los resultados en un archivo
results = {
    "total consultas": total_requests,
    "cache hits": cache_hits,
    "cache misses": cache_misses,
    "no encontrados": not_found,
    "hit_rate": hit_rate,
    "tiempo total ejecucion (s)": total_time,
    "tiempo promedio cache (ms)": tiempo_promedio_cache,
    "tiempo promedio almacenamiento (ms)": tiempo_promedio_no_cache,
    "tiempos cache (ms)": tiempos_cache,
    "tiempos almacenamiento (ms)": tiempos_no_cache,
    "tiempo cache (ms)": tiempo_cache,
    "tiempo total almacenamiento (ms)": tiempo_no_cache,
}

with open("/app/data/normal_traffic_results.json", 'w') as f:
    json.dump(results, f)

print(f"Resultados guardados en /app/data/normal_traffic_results.json")