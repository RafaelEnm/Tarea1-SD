#!/usr/bin/env python3

import json
import os
from glob import glob
from collections import Counter, defaultdict

def analyze_jsons(directory=None):
    """
    Analyze JSON files in specified directory, traverse "celdas" field,
    extract UUIDs from "alerts" fields and count repeated UUIDs.
    Show additional information (subtype, type, reportby, city) for each repeated UUID.
    """
    # Define path to jsons directory
    if directory is None:
        directory = "/app/data"
    
    # Make sure directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return
    
    # Search for all JSON files in directory
    json_files = glob(os.path.join(directory, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in directory '{directory}'.")
        return
    
    all_uuids = []
    uuid_info = defaultdict(list)  
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "celdas" not in data:
                print(f"Warning: File {json_file} does not contain 'celdas' field.")
                continue
            
            # Traverse each element in "celdas"
            for cell in data["celdas"]:
                # Check if "data" field exists
                if "data" not in cell:
                    continue
                
                # Check if "alerts" field exists in "data"
                if "alerts" not in cell["data"]:
                    continue
                
                # Extract UUIDs and additional info from "alerts"
                for alert in cell["data"]["alerts"]:
                    if "uuid" in alert:
                        uuid = alert["uuid"]
                        all_uuids.append(uuid)
                        
                        # Extract additional information
                        info = {
                            "subtype": alert.get("subtype", "N/A"),
                            "type": alert.get("type", "N/A"),
                            "reportby": alert.get("reportby", "N/A"),
                            "city": alert.get("city", "N/A"),
                            "file": os.path.basename(json_file)
                        }
                        
                        uuid_info[uuid].append(info)
        
        except json.JSONDecodeError:
            print(f"Error: File {json_file} is not a valid JSON.")
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
    
    # Count UUIDs 
    uuid_counter = Counter(all_uuids)
    
    # Filter only repeated UUIDs (that appear more than once)
    repeated_uuids = {uuid: count for uuid, count in uuid_counter.items() if count > 1}
    
    # Show results
    print(f"Analysis results:")
    print(f"- Total UUIDs found: {len(all_uuids)}")
    print(f"- Total unique UUIDs: {len(uuid_counter)}")
    print(f"- Total repeated UUIDs: {len(repeated_uuids)}")
    
    if repeated_uuids:
        print("\nRepeated UUIDs details:")
        for uuid, count in sorted(repeated_uuids.items(), key=lambda x: x[1], reverse=True):
            print(f"\n- UUID: {uuid}, appears {count} times:")
            
            # Show additional info for each instance of the UUID
            for idx, info in enumerate(uuid_info[uuid], 1):
                print(f"  Instance {idx}:")
                print(f"    Subtype: {info['subtype']}")
                print(f"    Type: {info['type']}")
                print(f"    Reportby: {info['reportby']}")
                print(f"    City: {info['city']}")
                print(f"    File: {info['file']}")
    else:
        print("\nNo repeated UUIDs found.")
    
    # Return number of repeated UUIDs
    return len(repeated_uuids)

if __name__ == "__main__":
    analyze_jsons()