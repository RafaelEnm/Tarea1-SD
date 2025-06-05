REGISTER '/opt/pig/lib/piggybank.jar';

-- Procesamiento de datos de alertas
alertas_raw = LOAD '/app/data/transformed_alerta_*.csv' USING PigStorage(',') AS (
    uuid:chararray, 
    city:chararray, 
    municipalityUser:chararray, 
    type:chararray, 
    street:chararray, 
    confidence:double, 
    location_x:double, 
    location_y:double, 
    fecha:chararray
);

alertas_sin_encabezado = FILTER alertas_raw BY uuid != 'uuid';

alertas_completas = FILTER alertas_sin_encabezado BY 
    (uuid IS NOT NULL AND uuid != '') AND
    (city IS NOT NULL AND city != '') AND
    (municipalityUser IS NOT NULL AND municipalityUser != '') AND
    (type IS NOT NULL AND type != '') AND
    (street IS NOT NULL AND street != '') AND
    (confidence IS NOT NULL) AND
    (location_x IS NOT NULL) AND
    (location_y IS NOT NULL) AND
    (fecha IS NOT NULL AND fecha != '');

alertas_agrupadas = GROUP alertas_completas BY uuid;
alertas_sin_duplicados = FOREACH alertas_agrupadas {
    ordenadas = ORDER alertas_completas BY fecha ASC;
    primera = LIMIT ordenadas 1;
    GENERATE FLATTEN(primera);
};

-- Procesamiento de datos de atascos/congestión
atascos_raw = LOAD '/app/data/transformed_atasco_*.csv' USING PigStorage(',') AS (
    uuid:chararray, 
    severity:int, 
    country:chararray, 
    length:int, 
    endnode:chararray, 
    roadtype:int, 
    speed:double, 
    street:chararray, 
    fecha:chararray, 
    region:chararray, 
    city:chararray
);

atascos_sin_encabezado = FILTER atascos_raw BY uuid != 'uuid';

atascos_completos = FILTER atascos_sin_encabezado BY 
    (uuid IS NOT NULL AND uuid != '') AND
    (severity IS NOT NULL) AND
    (country IS NOT NULL AND country != '') AND
    (length IS NOT NULL) AND
    (endnode IS NOT NULL AND endnode != '') AND
    (roadtype IS NOT NULL) AND
    (speed IS NOT NULL) AND
    (street IS NOT NULL AND street != '') AND
    (fecha IS NOT NULL AND fecha != '') AND
    (region IS NOT NULL AND region != '') AND
    (city IS NOT NULL AND city != '');

atascos_agrupados = GROUP atascos_completos BY uuid;
atascos_sin_duplicados = FOREACH atascos_agrupados {
    ordenados = ORDER atascos_completos BY fecha ASC;
    primero = LIMIT ordenados 1;
    GENERATE FLATTEN(primero);
};

-- Crear directorios con nombres más descriptivos
sh mkdir -p /app/results/reportes_ciudadanos_procesados;
sh mkdir -p /app/results/congestion_vehicular_procesada;

-- Almacenar datos procesados con nombres más claros
STORE alertas_sin_duplicados INTO '/app/results/reportes_ciudadanos_procesados/datos_reportes_limpios' USING PigStorage(',');

STORE atascos_sin_duplicados INTO '/app/results/congestion_vehicular_procesada/datos_congestion_limpios' USING PigStorage(',');

-- Crear archivos CSV finales con encabezados y nombres descriptivos
sh echo "uuid,city,municipalityUser,type,street,confidence,location_x,location_y,fecha" > /app/results/reportes_ciudadanos_procesados/encabezado_reportes.csv;
sh cat /app/results/reportes_ciudadanos_procesados/encabezado_reportes.csv /app/results/reportes_ciudadanos_procesados/datos_reportes_limpios/part-* > /app/results/reportes_ciudadanos_procesados/reportes_ciudadanos_final.csv;

sh echo "uuid,severity,country,length,endnode,roadtype,speed,street,fecha,region,city" > /app/results/congestion_vehicular_procesada/encabezado_congestion.csv;
sh cat /app/results/congestion_vehicular_procesada/encabezado_congestion.csv /app/results/congestion_vehicular_procesada/datos_congestion_limpios/part-* > /app/results/congestion_vehicular_procesada/congestion_vehicular_final.csv;

-- Conteo de registros para estadísticas de procesamiento
alertas_total = GROUP alertas_sin_encabezado ALL;
alertas_total_count = FOREACH alertas_total GENERATE COUNT(alertas_sin_encabezado) as count;
alertas_completas_total = GROUP alertas_completas ALL;
alertas_completas_count = FOREACH alertas_completas_total GENERATE COUNT(alertas_completas) as count;
alertas_sin_duplicados_total = GROUP alertas_sin_duplicados ALL;
alertas_sin_duplicados_count = FOREACH alertas_sin_duplicados_total GENERATE COUNT(alertas_sin_duplicados) as count;

atascos_total = GROUP atascos_sin_encabezado ALL;
atascos_total_count = FOREACH atascos_total GENERATE COUNT(atascos_sin_encabezado) as count;
atascos_completos_total = GROUP atascos_completos ALL;
atascos_completos_count = FOREACH atascos_completos_total GENERATE COUNT(atascos_completos) as count;
atascos_sin_duplicados_total = GROUP atascos_sin_duplicados ALL;
atascos_sin_duplicados_count = FOREACH atascos_sin_duplicados_total GENERATE COUNT(atascos_sin_duplicados) as count;

-- Mostrar estadísticas de procesamiento
DUMP alertas_total_count;
DUMP alertas_completas_count;
DUMP alertas_sin_duplicados_count;
DUMP atascos_total_count;
DUMP atascos_completos_count;
DUMP atascos_sin_duplicados_count;