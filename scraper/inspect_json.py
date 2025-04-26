import json
import os

# Buscar todos los archivos JSON en el directorio actual
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
print(f"Archivos JSON encontrados: {json_files}")

for file in json_files:
    print(f"\n--- Contenido de {file} ---")
    try:
        with open(file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                print(f"El archivo contiene un diccionario con {len(data)} claves:")
                print(list(data.keys()))
            elif isinstance(data, list):
                print(f"El archivo contiene una lista con {len(data)} elementos.")
                if data:
                    print("Primera entrada:")
                    print(json.dumps(data[0], indent=2))
            else:
                print(f"Tipo de datos: {type(data)}")
    except Exception as e:
        print(f"Error al leer {file}: {e}")