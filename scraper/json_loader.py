import os
import json
import glob
from pymongo import MongoClient
from bson import ObjectId
import time

# Environment configurations
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://admin:admin123@mongo:27017/')
MONGODB_DB = os.environ.get('MONGODB_DB', 'trafico_rm')
MONGODB_COLECCION_ALERTAS = os.environ.get('MONGODB_COLECCION_ALERTAS', 'alertas')
MONGODB_COLECCION_ATASCOS = os.environ.get('MONGODB_COLECCION_ATASCOS', 'atascos')

def load_json_to_mongodb(json_file):
    """
    Load Waze JSON data file to MongoDB
    """
    try:
        # Read JSON file
        with open(json_file, 'r') as file:
            print(f"Reading file: {json_file}")
            data = json.load(file)
        
        # Process JSON data
        total_alerts = 0
        total_jams = 0
        alerts_for_mongodb = []
        jams_for_mongodb = []
        
        # Extract all alerts and jams from cells
        for cell in data.get('celdas', []):
            if 'data' in cell:
                # Extract alerts
                for alert in cell['data'].get('alerts', []):
                    alerts_for_mongodb.append(alert)
                    total_alerts += 1
                
                # Extract jams
                for jam in cell['data'].get('jams', []):
                    jams_for_mongodb.append(jam)
                    total_jams += 1
        
        # Connect to MongoDB and insert data
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        alerts_collection = db[MONGODB_COLECCION_ALERTAS]
        jams_collection = db[MONGODB_COLECCION_ATASCOS]
        
        # Insert alerts to MongoDB
        alerts_inserted = 0
        if alerts_for_mongodb:
            try:
                result = alerts_collection.insert_many(alerts_for_mongodb, ordered=False)
                alerts_inserted = len(result.inserted_ids)
                print(f"Inserted {alerts_inserted} alerts to MongoDB")
                
                # Calculate duplicates
                duplicates = total_alerts - alerts_inserted
                if duplicates > 0:
                    print(f"Note: {duplicates} duplicate alerts were ignored")
                
            except Exception as e:
                if "duplicate key error" in str(e):
                    print(f"Error: Some or all alerts already existed in database")
                    # Try to extract number of inserted documents from error
                    try:
                        if hasattr(e, 'details') and 'nInserted' in e.details:
                            alerts_inserted = e.details['nInserted']
                            print(f"Approximately {alerts_inserted} alerts were inserted")
                    except:
                        pass
                else:
                    print(f"Error inserting alerts to MongoDB: {e}")
        
        # Insert jams to MongoDB
        jams_inserted = 0
        if jams_for_mongodb:
            try:
                result = jams_collection.insert_many(jams_for_mongodb, ordered=False)
                jams_inserted = len(result.inserted_ids)
                print(f"Inserted {jams_inserted} jams to MongoDB")
                
                # Calculate duplicates
                duplicates = total_jams - jams_inserted
                if duplicates > 0:
                    print(f"Note: {duplicates} duplicate jams were ignored")
                
            except Exception as e:
                if "duplicate key error" in str(e):
                    print(f"Error: Some or all jams already existed in database")
                    try:
                        if hasattr(e, 'details') and 'nInserted' in e.details:
                            jams_inserted = e.details['nInserted']
                            print(f"Approximately {jams_inserted} jams were inserted")
                    except:
                        pass
                else:
                    print(f"Error inserting jams to MongoDB: {e}")
        
        print(f"\nSummary for file {os.path.basename(json_file)}:")
        print(f"- Alerts found in JSON: {total_alerts}")
        print(f"- Jams found in JSON: {total_jams}")
        print(f"- Alerts inserted to MongoDB: {alerts_inserted}")
        print(f"- Jams inserted to MongoDB: {jams_inserted}")
        
        return True, alerts_inserted, jams_inserted
        
    except FileNotFoundError:
        print(f"Error: File {json_file} does not exist")
        return False, 0, 0
    except json.JSONDecodeError:
        print(f"Error: File {json_file} is not a valid JSON format")
        return False, 0, 0
    except Exception as e:
        print(f"Error processing file {json_file}: {e}")
        return False, 0, 0

def main():
    # Directory where JSON files will be searched
    jsons_dir = '/app/data'
    
    # Check if directory exists
    if not os.path.exists(jsons_dir):
        print(f"Error: Directory {jsons_dir} does not exist")
        return
    
    # Get list of JSON files
    json_files = glob.glob(os.path.join(jsons_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {jsons_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    # Connect to MongoDB and create indexes
    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        alerts_collection = db[MONGODB_COLECCION_ALERTAS]
        jams_collection = db[MONGODB_COLECCION_ATASCOS]
        
        # Create unique indexes on 'uuid' field if they don't exist
        alerts_collection.create_index(
            [("uuid", 1)],
            unique=True,
            name="unique_alert_uuid"
        )
        jams_collection.create_index(
            [("uuid", 1)],
            unique=True,
            name="unique_jam_uuid"
        )
        print("UUID indexes created/verified in MongoDB")
    except Exception as e:
        print(f"Error connecting to MongoDB or creating indexes: {e}")
        return
    
    # Total counters
    total_alerts_inserted = 0
    total_jams_inserted = 0
    files_processed = 0
    
    # Process each file
    for file in json_files:
        print(f"\nProcessing file {files_processed+1}/{len(json_files)}: {os.path.basename(file)}")
        result, alerts, jams = load_json_to_mongodb(file)
        
        if result:
            files_processed += 1
            total_alerts_inserted += alerts
            total_jams_inserted += jams
            
            # Wait one second between files to not overload MongoDB
            if files_processed < len(json_files):
                time.sleep(1)
    
    print("\n====== FINAL SUMMARY ======")
    print(f"Files processed: {files_processed}/{len(json_files)}")
    print(f"Total alerts inserted: {total_alerts_inserted}")
    print(f"Total jams inserted: {total_jams_inserted}")

if __name__ == "__main__":
    main()