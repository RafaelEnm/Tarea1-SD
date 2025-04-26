
import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Verificar archivos JSON disponibles
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
print(f"Archivos JSON encontrados: {json_files}")

# Cargar resultados de archivos individuales
results = []

# Intentar cargar archivo consolidado primero
if "all_simulation_results.json" in json_files:
    try:
        with open("all_simulation_results.json", "r") as f:
            results = json.load(f)
        print("✅ Datos cargados de all_simulation_results.json")
    except Exception as e:
        print(f"Error al cargar all_simulation_results.json: {e}")

# Si no hay resultados del archivo consolidado, cargar archivos individuales
if not results:
    for file in json_files:
        if file.startswith("results_") and file != "results_comparison.csv":
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    # Si el archivo contiene un solo resultado (diccionario)
                    if isinstance(data, dict):
                        results.append(data)
                    # Si contiene una lista de resultados
                    elif isinstance(data, list):
                        results.extend(data)
                print(f"✅ Datos cargados de {file}")
            except Exception as e:
                print(f"Error al cargar {file}: {e}")

# Verificar si tenemos datos para analizar
if not results:
    print("❌ No se pudieron cargar datos de ningún archivo JSON.")
    exit(1)

print(f"Total de resultados cargados: {len(results)}")

# Convertir a DataFrame para facilitar el análisis
df = pd.DataFrame(results)
print("\nColumnas disponibles en los datos:")
print(df.columns.tolist())

# Crear directorio para gráficos si no existe
if not os.path.exists("graficos"):
    os.makedirs("graficos")

# Verificar si tenemos las columnas necesarias
required_columns = ["distribution", "cache_policy", "hit_rate", "avg_latency", "hits", "misses"]
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    print(f"⚠️ Faltan algunas columnas esperadas: {missing_columns}")
    print("Mostrando las primeras filas de datos para inspección:")
    print(df.head())
else:
    # 1. Comparar hit rate por política de caché y distribución
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x="cache_policy", y="hit_rate", hue="distribution", data=df)
    plt.title("Tasa de Aciertos (Hit Rate) por Política de Caché y Distribución")
    plt.xlabel("Política de Caché")
    plt.ylabel("Hit Rate")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("graficos/hit_rate_comparison.png")
    print("✅ Gráfico de hit rate generado")

    # 2. Comparar latencia por política de caché y distribución
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x="cache_policy", y="avg_latency", hue="distribution", data=df)
    plt.title("Latencia Promedio por Política de Caché y Distribución")
    plt.xlabel("Política de Caché")
    plt.ylabel("Latencia Promedio (s)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("graficos/latency_comparison.png")
    print("✅ Gráfico de latencia generado")

    # 3. Mostrar la distribución de hits vs misses
    plt.figure(figsize=(14, 6))
    df_melted = pd.melt(df, 
                      id_vars=["distribution", "cache_policy"], 
                      value_vars=["hits", "misses"],
                      var_name="metric", value_name="value")
    
    sns.barplot(x="cache_policy", y="value", hue="metric", data=df_melted)
    plt.title("Distribución de Hits vs Misses por Política de Caché")
    plt.xlabel("Política de Caché")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.savefig("graficos/hits_misses_distribution.png")
    print("✅ Gráfico de hits vs misses generado")

    # 4. Crear tabla comparativa
    print("\nTabla Comparativa de Resultados:")
    comp_table = df[["distribution", "cache_policy", "hit_rate", "avg_latency", "hits", "misses"]]
    comp_table["hit_rate"] = comp_table["hit_rate"].apply(lambda x: f"{x:.2%}")
    comp_table["avg_latency"] = comp_table["avg_latency"].apply(lambda x: f"{x*1000:.2f} ms")
    print(comp_table.to_string(index=False))

    # Guardar la tabla como CSV para incluirla en el informe
    comp_table.to_csv("results_comparison.csv", index=False)
    print("✅ Tabla comparativa guardada como CSV")

print("\nAnálisis completo. Revisa los gráficos generados en la carpeta 'graficos'.")