import json
import os
from collections import defaultdict

def check_duplicates(json_file):
    """
    Check for duplicate UUIDs in a JSON file, distinguishing
    between alerts and jams.
    
    Parameters:
    json_file (str): Path to JSON file to analyze
    
    Returns:
    tuple: (duplicates, total_objects, unique_uuids, total_alerts, total_jams)
    """
    try:
        # Load JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Initialize UUID counter and their types
        uuid_count = defaultdict(int)
        uuid_type = {}  # To store the type (alert or jam)
        duplicates = {}
        total_objects = 0
        total_alerts = 0
        total_jams = 0
        
        # Search UUIDs in JSON
        if isinstance(data, dict):
            # If file has cell structure
            if "celdas" in data:
                for cell in data["celdas"]:
                    # Search in jams
                    if "data" in cell and "jams" in cell["data"]:
                        for jam in cell["data"]["jams"]:
                            if "uuid" in jam:
                                uuid = jam["uuid"]
                                uuid_count[uuid] += 1
                                if uuid not in uuid_type:
                                    uuid_type[uuid] = {"type": "jam"}
                                elif uuid_type[uuid]["type"] == "alert":
                                    uuid_type[uuid]["type"] = "mixed"  # UUID exists in both types
                                total_objects += 1
                                total_jams += 1
                    
                    # Search in alerts
                    if "data" in cell and "alerts" in cell["data"]:
                        for alert in cell["data"]["alerts"]:
                            if "uuid" in alert:
                                uuid = alert["uuid"]
                                uuid_count[uuid] += 1
                                if uuid not in uuid_type:
                                    uuid_type[uuid] = {"type": "alert"}
                                elif uuid_type[uuid]["type"] == "jam":
                                    uuid_type[uuid]["type"] = "mixed"  # UUID exists in both types
                                total_objects += 1
                                total_alerts += 1
        
        # If it's a direct list of objects
        elif isinstance(data, list):
            for obj in data:
                if "uuid" in obj:
                    uuid = obj["uuid"]
                    uuid_count[uuid] += 1
                    # Try to determine type based on present fields
                    if "roadType" in obj and "street" in obj:
                        obj_type = "jam"
                        total_jams += 1
                    elif "subtype" in obj and "reportRating" in obj:
                        obj_type = "alert"
                        total_alerts += 1
                    else:
                        obj_type = "unknown"
                    
                    if uuid not in uuid_type:
                        uuid_type[uuid] = {"type": obj_type}
                    elif uuid_type[uuid]["type"] != obj_type and obj_type != "unknown":
                        uuid_type[uuid]["type"] = "mixed"
                    
                    total_objects += 1
        
        # Filter only duplicate UUIDs
        for uuid, count in uuid_count.items():
            if count > 1:
                duplicates[uuid] = {
                    "count": count,
                    "type": uuid_type[uuid]["type"]
                }
        
        return duplicates, total_objects, len(uuid_count), total_alerts, total_jams
    
    except FileNotFoundError:
        print(f"Error: File '{json_file}' does not exist.")
        return {}, 0, 0, 0, 0
    except json.JSONDecodeError:
        print(f"Error: File '{json_file}' is not a valid JSON format.")
        return {}, 0, 0, 0, 0
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {}, 0, 0, 0, 0

def show_results(file, duplicates, total_objects, unique_uuids, total_alerts, total_jams):
    """Show analysis results for a file"""
    file_name = os.path.basename(file)
    
    if duplicates:
        print(f"\n{'=' * 20} FILE: {file_name} {'=' * 20}")
        print(f"Found {len(duplicates)} duplicate UUIDs in {total_objects} objects:")
        
        # Organize duplicates by type
        duplicates_by_type = {
            "alert": [],
            "jam": [],
            "mixed": []
        }
        
        for uuid, info in duplicates.items():
            duplicates_by_type[info["type"]].append((uuid, info["count"]))
        
        # Show alert duplicates
        if duplicates_by_type["alert"]:
            print("\n--- Duplicate UUIDs for ALERTS ---")
            for uuid, count in duplicates_by_type["alert"]:
                print(f"UUID: {uuid} - Appears {count} times")
        
        # Show jam duplicates
        if duplicates_by_type["jam"]:
            print("\n--- Duplicate UUIDs for JAMS ---")
            for uuid, count in duplicates_by_type["jam"]:
                print(f"UUID: {uuid} - Appears {count} times")
        
        # Show mixed duplicate UUIDs that appear in both types
        if duplicates_by_type["mixed"]:
            print("\n--- MIXED duplicate UUIDs (appear in alerts and jams) ---")
            for uuid, count in duplicates_by_type["mixed"]:
                print(f"UUID: {uuid} - Appears {count} times")
        
        # Calculate percentage of duplicates
        percentage = (len(duplicates) / unique_uuids) * 100 if unique_uuids > 0 else 0
        print(f"\nSummary for {file_name}:")
        print(f"Total objects analyzed: {total_objects} ({total_alerts} alerts, {total_jams} jams)")
        print(f"Unique UUIDs: {unique_uuids}")
        print(f"Duplicate UUIDs: {len(duplicates)} ({percentage:.2f}%)")
    else:
        print(f"\n{'=' * 20} FILE: {file_name} {'=' * 20}")
        print(f"No duplicate UUIDs found in this file.")
        print(f"Total objects analyzed: {total_objects} ({total_alerts} alerts, {total_jams} jams)")
        print(f"Unique UUIDs: {unique_uuids}")

def main():
    # Directory to search for JSON files
    json_dir = "/app/data"
    
    # Check if directory exists
    if not os.path.isdir(json_dir):
        print(f"Error: Directory '{json_dir}' does not exist.")
        return
    
    # Search for all JSON files in directory
    json_files = [os.path.join(json_dir, file) for file in os.listdir(json_dir) 
                 if file.endswith(".json")]
    
    if not json_files:
        print(f"No JSON files found in '{json_dir}'.")
        return
    
    print(f"Found {len(json_files)} JSON files to analyze.")
    
    # Global statistics
    total_files_with_duplicates = 0
    total_duplicates_found = 0
    
    # Process each JSON file
    for file in json_files:
        duplicates, total_objects, unique_uuids, total_alerts, total_jams = check_duplicates(file)
        
        # Show results for this file
        show_results(file, duplicates, total_objects, unique_uuids, total_alerts, total_jams)
        
        # Update global statistics
        if duplicates:
            total_files_with_duplicates += 1
            total_duplicates_found += len(duplicates)
    
    # Show global summary
    print(f"\n{'=' * 60}")
    print(f"GLOBAL SUMMARY:")
    print(f"Total files analyzed: {len(json_files)}")
    print(f"Files with duplicates: {total_files_with_duplicates}")
    print(f"Total duplicate UUIDs found: {total_duplicates_found}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()