-- data_aggregator.pig (Original Logic with Updated Output Filenames)

REGISTER '/opt/pig/lib/piggybank.jar';

-- Encontrar el directorio de ejecución más reciente para entrada
%declare latest_dir `ls -td /app/input/ejecucion_* | head -1`
%declare timestamp `date +%Y%m%d_%H%M%S`
%declare output_dir '/app/results/ejecucion_$timestamp'

-- Crear directorio para la ejecución actual
sh mkdir -p $output_dir;
sh echo "Usando datos de entrada de: $latest_dir";
sh echo "Guardando resultados en: $output_dir";

-- Cargar datos de alertas
alertas = LOAD '$latest_dir/alertas_completas/alertas_completas.csv' USING PigStorage(',') AS (
    uuid:chararray, city:chararray, municipalityUser:chararray, type:chararray, street:chararray,
    confidence:double, location_x:double, location_y:double, fecha:chararray
);

-- Cargar datos de atascos
atascos = LOAD '$latest_dir/atascos_completos/atascos_completos.csv' USING PigStorage(',') AS (
    uuid:chararray, severity:int, country:chararray, length:int, endnode:chararray,
    roadtype:int, speed:double, street:chararray, fecha:chararray, region:chararray, city:chararray
);

-- Extraer la hora de las alertas para análisis de hora pico
alertas_con_hora = FOREACH alertas GENERATE SUBSTRING(fecha, 11, 13) AS hora;
alertas_por_hora = GROUP alertas_con_hora BY hora;
conteo_alertas_por_hora = FOREACH alertas_por_hora GENERATE group AS hora, COUNT(alertas_con_hora) AS num_alertas;
horas_ordenadas = ORDER conteo_alertas_por_hora BY num_alertas DESC;
STORE horas_ordenadas INTO '$output_dir/peak_hours_data' USING PigStorage(',');
sh echo "hour,alert_count" > $output_dir/header_peak_hours.csv;
sh cat $output_dir/header_peak_hours.csv $output_dir/peak_hours_data/part-* > $output_dir/peak_hours.csv;

-- Calcular ciudades con más alertas
alertas_por_ciudad = GROUP alertas BY city;
conteo_alertas_por_ciudad = FOREACH alertas_por_ciudad GENERATE group AS city, COUNT(alertas) AS num_alertas;
ciudades_ordenadas = ORDER conteo_alertas_por_ciudad BY num_alertas DESC;
STORE ciudades_ordenadas INTO '$output_dir/sectors_alerts_data' USING PigStorage(',');
sh echo "sector,alert_count" > $output_dir/header_sectors_alerts.csv;
sh cat $output_dir/header_sectors_alerts.csv $output_dir/sectors_alerts_data/part-* > $output_dir/sectors_with_most_alerts.csv;

-- Calcular tipos de alerta más frecuentes
alertas_por_tipo = GROUP alertas BY type;
conteo_alertas_por_tipo = FOREACH alertas_por_tipo GENERATE group AS tipo_alerta, COUNT(alertas) AS num_alertas;
tipos_ordenados = ORDER conteo_alertas_por_tipo BY num_alertas DESC;
STORE tipos_ordenados INTO '$output_dir/alert_types_data' USING PigStorage(',');
sh echo "alert_type,quantity" > $output_dir/header_alert_types.csv;
sh cat $output_dir/header_alert_types.csv $output_dir/alert_types_data/part-* > $output_dir/alert_type_frequency.csv;

-- Filtrar alertas de tipo ACCIDENT
alertas_accident = FILTER alertas BY type == 'ACCIDENT';
accidentes_por_comuna = GROUP alertas_accident BY city;
conteo_accidentes_por_comuna = FOREACH accidentes_por_comuna GENERATE group AS comuna, COUNT(alertas_accident) AS num_accidentes;
comunas_ordenadas_por_accidentes = ORDER conteo_accidentes_por_comuna BY num_accidentes DESC;
STORE comunas_ordenadas_por_accidentes INTO '$output_dir/sectors_accidents_data' USING PigStorage(',');
sh echo "sector,accident_count" > $output_dir/header_sectors_accidents.csv;
sh cat $output_dir/header_sectors_accidents.csv $output_dir/sectors_accidents_data/part-* > $output_dir/sectors_with_most_accidents.csv;

-- Calcular calles con más alertas
alertas_por_calle = GROUP alertas BY street;
conteo_alertas_por_calle = FOREACH alertas_por_calle GENERATE group AS calle, COUNT(alertas) AS num_alertas;
calles_ordenadas = ORDER conteo_alertas_por_calle BY num_alertas DESC;
STORE calles_ordenadas INTO '$output_dir/streets_alerts_data' USING PigStorage(',');
sh echo "street,alert_count" > $output_dir/header_streets_alerts.csv;
sh cat $output_dir/header_streets_alerts.csv $output_dir/streets_alerts_data/part-* > $output_dir/streets_with_most_alerts.csv;

-- Calcular calles con mas accidentes
accidentes_group_by_calle_ciudad = GROUP alertas_accident BY (street, city);
conteo_accidentes_por_calle_ciudad = FOREACH accidentes_group_by_calle_ciudad GENERATE group.street AS calle, group.city AS ciudad, COUNT(alertas_accident) AS num_accidentes;
calles_ordenadas_por_accidentes = ORDER conteo_accidentes_por_calle_ciudad BY num_accidentes DESC;
STORE calles_ordenadas_por_accidentes INTO '$output_dir/streets_accidents_data' USING PigStorage(',');
sh echo "street,city,accident_count" > $output_dir/header_streets_accidents.csv;
sh cat $output_dir/header_streets_accidents.csv $output_dir/streets_accidents_data/part-* > $output_dir/streets_with_most_accidents.csv;

-- Análisis de atascos
atascos_por_ciudad = GROUP atascos BY city;
atascos_por_ciudad_sum = FOREACH atascos_por_ciudad GENERATE group AS ciudad, SUM(atascos.length) AS largo_total, COUNT(atascos) AS num_atascos;
atascos_ciudades_ordenados = ORDER atascos_por_ciudad_sum BY largo_total DESC;
STORE atascos_ciudades_ordenados INTO '$output_dir/jams_by_city_data' USING PigStorage(',');
sh echo "city,total_length,jam_count" > $output_dir/header_jams_city.csv;
sh cat $output_dir/header_jams_city.csv $output_dir/jams_by_city_data/part-* > $output_dir/jams_by_city.csv;

-- Mensaje para el registro
DUMP (GROUP alertas ALL), (GROUP atascos ALL);