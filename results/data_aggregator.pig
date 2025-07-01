-- data_aggregator.pig (v2 - Robust Types)
-- Purpose: Takes cleaned data and aggregates it. Now with explicit type casting for robustness.

REGISTER '/opt/pig/lib/piggybank.jar';

-- Declare paths
%declare latest_dir `ls -td /app/input/ejecucion_* | head -1`
%declare timestamp `date +%Y%m%d_%H%M%S`
%declare output_dir '/app/results/ejecucion_$timestamp'

-- Create output directory and log paths
sh mkdir -p $output_dir;
sh echo "Using input data from: $latest_dir";
sh echo "Saving aggregation results to: $output_dir";

-- ============================================================
-- DATA LOADING (WITH EXPLICIT TYPE CASTING)
-- ============================================================

-- Load complete alerts data, casting numeric fields to prevent errors
alerts = LOAD '$latest_dir/alerts_complete/complete_alerts.csv' USING PigStorage(',') AS (
    uuid:chararray, 
    city:chararray, 
    municipalityUser:chararray, 
    type:chararray, 
    street:chararray,
    confidence:double,        -- Cast to double
    location_x:double,        -- Cast to double
    location_y:double,        -- Cast to double
    date:chararray
);

-- Load complete jams data, casting numeric fields to prevent errors
jams = LOAD '$latest_dir/jams_complete/complete_jams.csv' USING PigStorage(',') AS (
    uuid:chararray, 
    severity:int,             -- Cast to integer
    country:chararray, 
    length:int,               -- Cast to integer
    endnode:chararray,
    roadtype:int,             -- Cast to integer
    speed:double,             -- Cast to double
    street:chararray, 
    date:chararray, 
    region:chararray, 
    city:chararray
);

-- ============================================================
-- DATA AGGREGATION (This part now operates on safely casted data)
-- ============================================================

-- 1. Peak Hours Analysis (from alerts)
alerts_with_hour = FOREACH alerts GENERATE SUBSTRING(date, 11, 13) AS hour;
alerts_by_hour = GROUP alerts_with_hour BY hour;
peak_hours_count = FOREACH alerts_by_hour GENERATE group AS hour, COUNT(alerts_with_hour) AS alert_count;
peak_hours_sorted = ORDER peak_hours_count BY alert_count DESC;
STORE peak_hours_sorted INTO '$output_dir/peak_hours_data' USING PigStorage(',');
sh echo "hour,alert_count" > $output_dir/header_peak_hours.csv;
sh cat $output_dir/header_peak_hours.csv $output_dir/peak_hours_data/part-* > $output_dir/peak_hours.csv;

-- 2. Sectors (cities/municipalities) with the most alerts
alerts_by_sector = GROUP alerts BY city;
sector_alert_count = FOREACH alerts_by_sector GENERATE group AS sector, COUNT(alerts) AS alert_count;
sectors_sorted_by_alerts = ORDER sector_alert_count BY alert_count DESC;
STORE sectors_sorted_by_alerts INTO '$output_dir/sectors_alerts_data' USING PigStorage(',');
sh echo "sector,alert_count" > $output_dir/header_sectors_alerts.csv;
sh cat $output_dir/header_sectors_alerts.csv $output_dir/sectors_alerts_data/part-* > $output_dir/sectors_with_most_alerts.csv;

-- 3. Most frequent alert types
alerts_by_type = GROUP alerts BY type;
type_count = FOREACH alerts_by_type GENERATE group AS alert_type, COUNT(alerts) AS quantity;
types_sorted = ORDER type_count BY quantity DESC;
STORE types_sorted INTO '$output_dir/alert_types_data' USING PigStorage(',');
sh echo "alert_type,quantity" > $output_dir/header_alert_types.csv;
sh cat $output_dir/header_alert_types.csv $output_dir/alert_types_data/part-* > $output_dir/alert_type_frequency.csv;

-- 4. Sectors with the most accidents (type 'ACCIDENT')
accident_alerts = FILTER alerts BY type == 'ACCIDENT';
accidents_by_sector = GROUP accident_alerts BY city;
sector_accident_count = FOREACH accidents_by_sector GENERATE group AS sector, COUNT(accident_alerts) AS accident_count;
sectors_sorted_by_accidents = ORDER sector_accident_count BY accident_count DESC;
STORE sectors_sorted_by_accidents INTO '$output_dir/sectors_accidents_data' USING PigStorage(',');
sh echo "sector,accident_count" > $output_dir/header_sectors_accidents.csv;
sh cat $output_dir/header_sectors_accidents.csv $output_dir/sectors_accidents_data/part-* > $output_dir/sectors_with_most_accidents.csv;

-- 5. Streets with the most alerts
alerts_by_street = GROUP alerts BY street;
street_alert_count = FOREACH alerts_by_street GENERATE group AS street, COUNT(alerts) AS alert_count;
streets_sorted_by_alerts = ORDER street_alert_count BY alert_count DESC;
STORE streets_sorted_by_alerts INTO '$output_dir/streets_alerts_data' USING PigStorage(',');
sh echo "street,alert_count" > $output_dir/header_streets_alerts.csv;
sh cat $output_dir/header_streets_alerts.csv $output_dir/streets_alerts_data/part-* > $output_dir/streets_with_most_alerts.csv;

-- 6. Streets with the most accidents
accidents_by_street = GROUP accident_alerts BY (street, city);
street_accident_count = FOREACH accidents_by_street GENERATE group.street AS street, group.city AS city, COUNT(accident_alerts) AS accident_count;
streets_sorted_by_accidents = ORDER street_accident_count BY accident_count DESC;
STORE streets_sorted_by_accidents INTO '$output_dir/streets_accidents_data' USING PigStorage(',');
sh echo "street,city,accident_count" > $output_dir/header_streets_accidents.csv;
sh cat $output_dir/header_streets_accidents.csv $output_dir/streets_accidents_data/part-* > $output_dir/streets_with_most_accidents.csv;

-- 7. Jams analysis by city (total length and count)
jams_by_city = GROUP jams BY city;
jams_agg_by_city = FOREACH jams_by_city GENERATE group AS city, SUM(jams.length) AS total_length, COUNT(jams) AS jam_count;
jams_by_city_sorted = ORDER jams_agg_by_city BY total_length DESC;
STORE jams_by_city_sorted INTO '$output_dir/jams_by_city_data' USING PigStorage(',');
sh echo "city,total_length,jam_count" > $output_dir/header_jams_city.csv;
sh cat $output_dir/header_jams_city.csv $output_dir/jams_by_city_data/part-* > $output_dir/jams_by_city.csv;

-- Display final counts for logging
alert_count_total = FOREACH (GROUP alerts ALL) GENERATE COUNT(alerts);
jam_count_total = FOREACH (GROUP jams ALL) GENERATE COUNT(jams);
DUMP alert_count_total;
DUMP jam_count_total;