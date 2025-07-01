-- debug_aggregator.pig
-- PROPÓSITO: Solo cargar los datos y contar los registros para depuración.

-- Declarar la ruta de entrada
%declare latest_dir `ls -td /app/input/ejecucion_* | head -1`

-- Mensaje de depuración para saber qué directorio se está usando
sh echo "DEBUG: Intentando cargar datos desde el directorio: $latest_dir";

-- Cargar los datos con el esquema que esperamos
alerts = LOAD '$latest_dir/alerts_complete/complete_alerts.csv' USING PigStorage(',') AS (
    uuid:chararray, city:chararray, municipalityUser:chararray, type:chararray, street:chararray,
    confidence:double, location_x:double, location_y:double, date:chararray
);

jams = LOAD '$latest_dir/jams_complete/complete_jams.csv' USING PigStorage(',') AS (
    uuid:chararray, severity:int, country:chararray, length:int, endnode:chararray,
    roadtype:int, speed:double, street:chararray, date:chararray, region:chararray, city:chararray
);

-- Agrupar TODO para poder contar
grouped_alerts = GROUP alerts ALL;
grouped_jams = GROUP jams ALL;

-- Contar los registros
alert_count = FOREACH grouped_alerts GENERATE COUNT(alerts);
jam_count = FOREACH grouped_jams GENERATE COUNT(jams);

-- Mostrar los resultados en la terminal. ¡ESTO ES LO MÁS IMPORTANTE!
DUMP alert_count;
DUMP jam_count;