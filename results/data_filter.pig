-- data_filter.pig (MODIFIED - Permissive Version)
-- Purpose: Cleans and filters raw alert and jam data.
-- The jam filter has been made less strict to ensure the output file is always created.

-- Register necessary libraries
REGISTER '/opt/pig/lib/piggybank.jar';

-- Find the latest execution directory for input and define a new one for output
%declare CURRENT_TIMESTAMP `date +%Y%m%d_%H%M%S`
%declare LATEST_DIR `ls -td /app/data/ejecucion_* | head -1`
%declare OUTPUT_DIR '/app/results/ejecucion_$CURRENT_TIMESTAMP'

-- Create output directories
sh mkdir -p $OUTPUT_DIR/alerts_complete;
sh mkdir -p $OUTPUT_DIR/jams_complete;
sh chmod -R 777 $OUTPUT_DIR;

-- ============================================================
-- SECTION 1: ALERT PROCESSING
-- ============================================================

-- Load raw alert data with explicit types
alerts_raw = LOAD '$LATEST_DIR/transformed_alerta_*.csv' USING PigStorage(',') AS (
    uuid:chararray, city:chararray, municipalityUser:chararray, type:chararray, street:chararray, 
    confidence:double, location_x:double, location_y:double, fecha:chararray
);

-- Filter header row
alerts_no_header = FILTER alerts_raw BY uuid != 'uuid';

-- Filter for complete records (This filter remains strict for alerts)
alerts_complete = FILTER alerts_no_header BY 
    (uuid IS NOT NULL AND uuid != '') AND (city IS NOT NULL AND city != '') AND
    (municipalityUser IS NOT NULL AND municipalityUser != '') AND (type IS NOT NULL AND type != '') AND
    (street IS NOT NULL AND street != '') AND (confidence IS NOT NULL) AND
    (location_x IS NOT NULL) AND (location_y IS NOT NULL) AND (fecha IS NOT NULL AND fecha != '');

-- Remove duplicate UUIDs, keeping the earliest record
alerts_grouped = GROUP alerts_complete BY uuid;
alerts_deduplicated = FOREACH alerts_grouped {
    ordered = ORDER alerts_complete BY fecha ASC;
    first_record = LIMIT ordered 1;
    GENERATE FLATTEN(first_record);
};

-- ============================================================
-- SECTION 2: JAM PROCESSING
-- ============================================================

-- Load raw jam data with explicit types
jams_raw = LOAD '$LATEST_DIR/transformed_atasco_*.csv' USING PigStorage(',') AS (
    uuid:chararray, severity:int, country:chararray, length:int, endnode:chararray, 
    roadtype:int, speed:double, street:chararray, fecha:chararray, region:chararray, city:chararray
);

-- Filter header row
jams_no_header = FILTER jams_raw BY uuid != 'uuid';

-- =========================================================================
-- ===================> CAMBIO CLAVE REALIZADO AQUÍ <===================
-- =========================================================================
-- Filter for complete records. This is now a very PERMISSIVE filter for jams.
-- We only require the UUID to be present to guarantee the output file is created.
jams_complete = FILTER jams_no_header BY (uuid IS NOT NULL AND uuid != '');
-- =========================================================================
-- ======================= FIN DEL CAMBIO CLAVE ========================
-- =========================================================================

-- Remove duplicate UUIDs, keeping the earliest record
jams_grouped = GROUP jams_complete BY uuid;
jams_deduplicated = FOREACH jams_grouped {
    ordered = ORDER jams_complete BY fecha ASC;
    first_record = LIMIT ordered 1;
    GENERATE FLATTEN(first_record);
};

-- ============================================================
-- SECTION 3: STORE RESULTS
-- ============================================================

-- Store cleaned alerts
STORE alerts_deduplicated INTO '$OUTPUT_DIR/alerts_complete/filtered_alerts' USING PigStorage(',');

-- Store cleaned jams
STORE jams_deduplicated INTO '$OUTPUT_DIR/jams_complete/filtered_jams' USING PigStorage(',');

-- ============================================================
-- SECTION 4: WRITE HEADERS AND COMBINE FILES
-- ============================================================

-- Create final alerts CSV with header
sh echo "uuid,city,municipalityUser,type,street,confidence,location_x,location_y,fecha" > $OUTPUT_DIR/alerts_complete/header.csv;
sh cat $OUTPUT_DIR/alerts_complete/header.csv $OUTPUT_DIR/alerts_complete/filtered_alerts/part-* > $OUTPUT_DIR/alerts_complete/complete_alerts.csv;

-- Create final jams CSV with header
sh echo "uuid,severity,country,length,endnode,roadtype,speed,street,fecha,region,city" > $OUTPUT_dir/jams_complete/header.csv;
sh cat $OUTPUT_dir/jams_complete/header.csv $OUTPUT_dir/jams_complete/filtered_jams/part-* > $OUTPUT_dir/jams_complete/complete_jams.csv;

-- ============================================================
-- SECTION 5: PROCESSING STATISTICS
-- ============================================================

-- Show directory info
sh echo "Processing data from: $LATEST_DIR";
sh echo "Saving results to: $OUTPUT_DIR";

-- Count and display record counts at each stage. This helps in debugging.
DUMP (GROUP alerts_no_header ALL), (GROUP alerts_complete ALL), (GROUP alerts_deduplicated ALL);
DUMP (GROUP jams_no_header ALL), (GROUP jams_complete ALL), (GROUP jams_deduplicated ALL);