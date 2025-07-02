from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime
import pandas as pd
import os
import glob
import time
import json

def export_mongo_to_elasticsearch():
    """Exporta directamente desde MongoDB a Elasticsearch usando bulk operations"""
    
    print("**Indexing MongoDB data to Elasticsearch")
    
    # Conectar a MongoDB
    try:
        mongo_client = MongoClient('mongodb://admin:admin123@mongo:27017/')
        db = mongo_client['trafico_rm']
        mongo_client.admin.command('ping')
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False
    
    # Conectar a Elasticsearch
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return False
    
    # Función auxiliar para preparar documentos
    def prepare_docs_for_bulk(collection, index_name):
        """Prepara documentos para bulk insert"""
        for doc in collection.find({}):
            # Extraer el _id y eliminarlo del documento
            doc_id = str(doc.pop('_id'))
            
            yield {
                "_index": index_name,
                "_id": doc_id,
                "_source": doc
            }
    
    # Exportar alertas
    try:
        alertas_collection = db['alertas']
        alertas_count = alertas_collection.count_documents({})
        
        if alertas_count > 0:
            # Usar bulk helper
            success, failed = bulk(
                es,
                prepare_docs_for_bulk(alertas_collection, "waze_alertas"),
                chunk_size=1000,
                request_timeout=60
            )
            
            print(f"Alertas inserted: {success}")
        else:
            print("No alertas found in MongoDB")
        
    except Exception as e:
        print(f"Error processing alertas: {e}")
    
    # Exportar atascos
    try:
        atascos_collection = db['atascos']
        atascos_count = atascos_collection.count_documents({})
        
        if atascos_count > 0:
            # Usar bulk helper
            success, failed = bulk(
                es,
                prepare_docs_for_bulk(atascos_collection, "waze_atascos"),
                chunk_size=1000,
                request_timeout=60
            )
            
            print(f"Atascos inserted: {success}")
        else:
            print("No atascos found in MongoDB")
        
    except Exception as e:
        print(f"Error processing atascos: {e}")
    
    # Cerrar conexiones
    mongo_client.close()
    print("**MongoDB indexing completed")
    return True

def export_processed_data_to_elasticsearch():
    """Exporta los datos procesados (CSV) desde la carpeta results/processed"""
    
    print("**Indexing processed CSV data to Elasticsearch")
    
    # Conectar a Elasticsearch
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return False
    
    # Buscar la carpeta de ejecución más reciente en processed
    try:
        processed_path = "/app/input"  # results/processed montado aquí
        
        # Buscar carpetas que empiecen con "ejecucion_"
        ejecucion_folders = glob.glob(os.path.join(processed_path, "ejecucion_*"))
        
        if not ejecucion_folders:
            print(f"No execution folders found in {processed_path}")
            # Buscar directamente archivos CSV en el directorio raíz
            csv_files = glob.glob(os.path.join(processed_path, "*.csv"))
            if csv_files:
                latest_folder = processed_path
                print(f"Found CSV files directly in {processed_path}")
            else:
                return False
        else:
            # Ordenar por nombre (incluye timestamp)
            latest_folder = max(ejecucion_folders)
            print(f"Using latest execution folder: {os.path.basename(latest_folder)}")
        
    except Exception as e:
        print(f"Error finding execution folder: {e}")
        return False
    
    # Buscar archivos CSV
    try:
        csv_files = glob.glob(os.path.join(latest_folder, "*.csv"))
        
        if not csv_files:
            print(f"No CSV files found in {latest_folder}")
            return False
        
        print(f"CSV files found: {len(csv_files)}")
        for csv_file in csv_files:
            print(f"  - {os.path.basename(csv_file)}")
        
    except Exception as e:
        print(f"Error searching CSV files: {e}")
        return False
    
    # Función para preparar documentos CSV para bulk
    def prepare_csv_for_bulk(csv_file_path):
        """Convierte CSV a documentos para Elasticsearch"""
        try:
            # Leer CSV
            df = pd.read_csv(csv_file_path)
            
            if df.empty:
                print(f"Empty CSV file: {csv_file_path}")
                return
            
            # Obtener nombre del archivo sin extensión
            file_name = os.path.splitext(os.path.basename(csv_file_path))[0]
            
            # Crear índice específico para cada tipo de análisis
            # Usar prefijo más descriptivo
            if "congestion" in file_name.lower():
                index_name = "analisis_congestion"
            elif "ciudadanos" in file_name.lower():
                index_name = "analisis_reportes_ciudadanos"
            elif "waze" in file_name.lower():
                index_name = "analisis_waze"
            else:
                index_name = f"analisis_{file_name.lower()}"
            
            print(f"Processing {file_name} -> {index_name} ({len(df)} records)")
            
            # Convertir cada fila a documento
            for idx, row in df.iterrows():
                doc = row.to_dict()
                
                # Limpiar valores NaN/None
                doc = {k: (v if pd.notna(v) else None) for k, v in doc.items()}
                
                # Agregar metadatos
                doc['archivo_origen'] = file_name
                doc['fecha_procesamiento'] = datetime.now().isoformat()
                doc['tipo_analisis'] = file_name.replace('_procesada', '').replace('_', ' ').title()
                
                # Usar combinación de archivo y fila como ID único
                doc_id = f"{file_name}_{idx}"
                
                yield {
                    "_index": index_name,
                    "_id": doc_id,
                    "_source": doc
                }
                
        except Exception as e:
            print(f"Error processing {csv_file_path}: {e}")
            return
    
    # Procesar cada archivo CSV
    total_success = 0
    total_failed = 0
    indices_creados = []
    
    for csv_file in csv_files:
        try:
            file_name = os.path.basename(csv_file)
            print(f"\n**Processing: {file_name}")
            
            # Usar bulk helper
            success, failed = bulk(
                es,
                prepare_csv_for_bulk(csv_file),
                chunk_size=500,  # Reducido para mejor manejo de memoria
                request_timeout=60
            )
            
            total_success += success
            total_failed += len(failed) if failed else 0
            
            # Determinar nombre del índice
            file_base = os.path.splitext(file_name)[0]
            if "congestion" in file_base.lower():
                index_name = "analisis_congestion"
            elif "ciudadanos" in file_base.lower():
                index_name = "analisis_reportes_ciudadanos"
            elif "waze" in file_base.lower():
                index_name = "analisis_waze"
            else:
                index_name = f"analisis_{file_base.lower()}"
            
            if index_name not in indices_creados:
                indices_creados.append(index_name)
            
            print(f"✓ {file_name}: {success} records indexed")
            
        except Exception as e:
            print(f"✗ Error processing {file_name}: {e}")
            total_failed += 1
    
    print(f"\n**CSV indexing completed")
    print(f"Total records indexed: {total_success}")
    print(f"Total files processed: {len(csv_files)}")
    print(f"Indices created: {', '.join(indices_creados)}")
    
    return total_success > 0

def export_raw_data_to_elasticsearch():
    """Exporta datos de export (JSON) si existen"""
    
    print("**Checking for raw export data")
    
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return False
    
    # Buscar archivos JSON en export
    export_path = "/app/filtered"  # results/output montado aquí si es necesario
    if os.path.exists(export_path):
        json_files = glob.glob(os.path.join(export_path, "*.json"))
        
        if json_files:
            print(f"Found {len(json_files)} JSON files to process")
            
            for json_file in json_files:
                try:
                    file_name = os.path.splitext(os.path.basename(json_file))[0]
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Si es una lista de objetos
                    if isinstance(data, list):
                        docs_to_index = []
                        for idx, item in enumerate(data):
                            docs_to_index.append({
                                "_index": f"export_{file_name}",
                                "_id": f"{file_name}_{idx}",
                                "_source": {
                                    **item,
                                    "archivo_origen": file_name,
                                    "fecha_procesamiento": datetime.now().isoformat()
                                }
                            })
                        
                        success, failed = bulk(es, docs_to_index, chunk_size=1000)
                        print(f"✓ {file_name}: {success} records indexed")
                    
                except Exception as e:
                    print(f"✗ Error processing {json_file}: {e}")
        else:
            print("No JSON export files found")
    else:
        print("Export path not found, skipping raw data export")
    
    return True

def wait_for_services():
    """Espera a que los servicios estén disponibles antes de proceder"""
    
    max_retries = 30
    retry_count = 0
    
    print("Waiting for services to be ready...")
    
    while retry_count < max_retries:
        try:
            # Probar MongoDB
            mongo_client = MongoClient('mongodb://admin:admin123@mongo:27017/', serverSelectionTimeoutMS=5000)
            mongo_client.admin.command('ping')
            mongo_client.close()
            
            # Probar Elasticsearch
            es = Elasticsearch("http://elasticsearch:9200", request_timeout=5)
            if es.ping():
                print("✓ All services are ready")
                return True
            
        except Exception as e:
            retry_count += 1
            print(f"Attempt {retry_count}/{max_retries} - Services not ready yet...")
            time.sleep(10)
    
    print("✗ Services not available after maximum retries")
    return False

if __name__ == "__main__":
    # Esperar a que los servicios estén listos
    if not wait_for_services():
        exit(1)
    
    print("="*60)
    print("ELASTICSEARCH UPLOADER - Starting indexing process")
    print("="*60)
    
    success_count = 0
    
    # 1. Exportar desde MongoDB (datos raw)
    print("\n1. MONGODB DATA")
    if export_mongo_to_elasticsearch():
        success_count += 1
    
    # 2. Exportar datos procesados (CSV)
    print("\n2. PROCESSED DATA (CSV)")
    if export_processed_data_to_elasticsearch():
        success_count += 1
    
    # 3. Exportar datos de export si existen
    print("\n3. EXPORT DATA (JSON)")
    if export_raw_data_to_elasticsearch():
        success_count += 1
    
    print("\n" + "="*60)
    if success_count >= 2:  # Al menos MongoDB y CSV processed
        print("✅ INDEXING COMPLETED SUCCESSFULLY")
        print("Data is now available in Elasticsearch and can be visualized in Kibana")
    else:
        print("⚠️  INDEXING COMPLETED WITH ERRORS")
        print("Some data sources could not be processed")
        exit(1)
    print("="*60)