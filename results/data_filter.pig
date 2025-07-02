-- data_filter.pig (Final Corrected Version)
-- Fixed the deduplication logic inside the FOREACH block.

REGISTER '/opt/pig/lib/piggybank.jar';

-- Declare paths
%declare CURRENT_TIMESTAMP `date +%Y%m%d_%H%M%S`
%declare LATEST_DIR `ls -td /app/data/ejecucion_* | head -1`
%declare OUTPUT_DIR '/app/results/ejecucion_$CURRENT_TIMESTAMP'

-- Create output directories
sh mkdir -p $OUTPUT_DIR/alertas_completas;
sh mkdir -p $OUTPUT_DIR/atascos_completos;
sh chmod -R 777 $OUTPUT_DIR;

-- ============================================================
-- ALERT PROCESSING
-- ============================================================
alerts_raw = LOAD '$LATEST_DIR/transformed_alerta_*.csv' USING PigStorage(',') AS (uuid:chararray, city:chararray, municipalityUser:chararray, type:chararray, street:chararray, confidence:double, location_x:double, location_y:double, fecha:chararray);
alerts_no_header = FILTER alerts_raw BY uuid != 'uuid';
alerts_complete = FILTER alerts_no_header BY (uuid IS NOT NULL AND uuid != '') AND (city IS NOT NULL AND city != '') AND (municipalityUser IS NOT NULL AND municipalityUser != '') AND (type IS NOT NULL AND type != '') AND (street IS NOT NULL AND street != '') AND (confidence IS NOT NULL) AND (location_x IS NOT NULL) AND (location_y IS NOT NULL) AND (fecha IS NOT NULL AND fecha != '');

-- --- CORRECCIÓN LÓGICA ---
alertas_agrupadas = GROUP alerts_complete BY uuid;
alertas_sin_duplicados = FOREACH alertas_agrupadas {
    ordenadas = ORDER alerts_completas BY fecha ASC;
    primera = LIMIT ordenadas 1;
    GENERATE FLATTEN(primera);
};

-- ============================================================
-- JAM PROCESSING
-- ============================================================
atascos_raw = LOAD '$LATEST_DIR/transformed_atasco_*.csv' USING PigStorage(',') AS (uuid:chararray, severity:int, country:chararray, length:int, endnode:chararray, roadtype:int, speed:double, street:chararray, fecha:chararray, region:chararray, city:chararray);
atascos_no_header = FILTER atascos_raw BY uuid != 'uuid';
atascos_completos = FILTER atascos_no_header BY (uuid IS NOT NULL AND uuid != ''); -- Filtro permisivo

-- --- CORRECCIÓN LÓGICA ---
atascos_agrupados = GROUP atascos_completos BY uuid;
atascos_sin_duplicados = FOREACH atascos_agrupados {
    ordenados = ORDER atascos_completos BY fecha ASC;
    primero = LIMIT ordenados 1;
    GENERATE FLATTEN(primero);
};

-- ============================================================
-- STORE RESULTS AND WRITE HEADERS
-- ============================================================
STORE alertas_sin_duplicados INTO '$OUTPUT_DIR/alertas_completas/alertas_filtradas' USING PigStorage(',');
STORE atascos_sin_duplicados INTO '$OUTPUT_DIR/atascos_completos/atascos_filtrados' USING PigStorage(',');

sh echo "uuid,city,municipalityUser,type,street,confidence,location_x,location_y,fecha" > $OUTPUT_DIR/alertas_completas/encabezado.csv;
sh cat $OUTPUT_DIR/alertas_completas/encabezado.csv $OUTPUT_DIR/alertas_completas/alertas_filtradas/part-* > $OUTPUT_DIR/alertas_completas/alertas_completas.csv;

sh echo "uuid,severity,country,length,endnode,roadtype,speed,street,fecha,region,city" > $OUTPUT_DIR/atascos_completos/encabezado.csv;
sh cat $OUTPUT_DIR/atascos_completos/encabezado.csv $OUTPUT_DIR/atascos_completos/atascos_filtrados/part-* > $OUTPUT_DIR/atascos_completos/atascos_completos.csv;