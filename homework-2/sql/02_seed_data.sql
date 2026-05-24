SET search_path TO oilfield, public;

SELECT setseed(0.42);

INSERT INTO wells (well_name, field_name, region, well_type, drill_date, depth_m, is_active) VALUES
    ('W-001', 'Самотлорское',   'ХМАО',           'oil',   '2015-03-12', 2850.50, TRUE),
    ('W-002', 'Самотлорское',   'ХМАО',           'oil',   '2016-07-08', 3100.00, TRUE),
    ('W-003', 'Приобское',      'ХМАО',           'oil',   '2014-11-20', 2780.00, TRUE),
    ('W-004', 'Приобское',      'ХМАО',           'mixed', '2017-02-14', 2950.75, TRUE),
    ('W-005', 'Ванкорское',     'Красноярский край','oil',  '2018-05-22', 3200.00, TRUE),
    ('W-006', 'Ванкорское',     'Красноярский край','gas',  '2018-09-11', 3050.00, TRUE),
    ('W-007', 'Уренгойское',    'ЯНАО',           'gas',   '2013-04-03', 3400.50, TRUE),
    ('W-008', 'Уренгойское',    'ЯНАО',           'gas',   '2019-08-19', 3380.00, TRUE),
    ('W-009', 'Ромашкинское',   'Татарстан',      'oil',   '2012-10-05', 1850.00, TRUE),
    ('W-010', 'Ромашкинское',   'Татарстан',      'oil',   '2020-01-15', 1920.25, FALSE);

INSERT INTO production (well_id, prod_date, oil_tons, gas_m3, water_tons, downtime_hours)
SELECT
    w.well_id,
    d::date AS prod_date,
    CASE
        WHEN w.well_type = 'gas' THEN ROUND((random()*15 + 5)::numeric, 2)
        ELSE ROUND((random()*60 + 30 + (w.well_id * 5))::numeric, 2)
    END AS oil_tons,
    CASE
        WHEN w.well_type = 'gas' THEN ROUND((random()*40000 + 10000)::numeric, 2)
        ELSE ROUND((random()*5000 + 1000)::numeric, 2)
    END AS gas_m3,
    ROUND((random()*20 + 5)::numeric, 2) AS water_tons,
    CASE WHEN random() < 0.85 THEN 0
         WHEN random() < 0.97 THEN ROUND((random()*4)::numeric, 2)
         ELSE ROUND((random()*20 + 4)::numeric, 2)
    END AS downtime_hours
FROM wells w
CROSS JOIN generate_series('2025-01-01'::date, '2025-03-31'::date, '1 day'::interval) d
WHERE w.is_active;

UPDATE production SET oil_tons = NULL
WHERE production_id IN (SELECT production_id FROM production ORDER BY random() LIMIT 15);
UPDATE production SET water_tons = NULL
WHERE production_id IN (SELECT production_id FROM production ORDER BY random() LIMIT 10);

INSERT INTO telemetry (well_id, ts, pressure_bar, temperature_c, power_kw, pump_hours)
SELECT
    w.well_id,
    ts,
    ROUND((random()*40 + 150 + (w.well_id*2))::numeric, 2) AS pressure_bar,
    ROUND((random()*25 + 60)::numeric, 2)                 AS temperature_c,
    ROUND((random()*200 + 400)::numeric, 2)               AS power_kw,
    ROUND((random()*0.5 + 0.5)::numeric, 2)               AS pump_hours
FROM wells w
CROSS JOIN generate_series(
    '2025-01-01 00:00'::timestamp,
    '2025-03-31 23:00'::timestamp,
    '1 hour'::interval
) ts
WHERE w.is_active;

UPDATE telemetry SET pressure_bar = NULL
WHERE telemetry_id IN (SELECT telemetry_id FROM telemetry ORDER BY random() LIMIT 50);
UPDATE telemetry SET pressure_bar = pressure_bar * 3
WHERE telemetry_id IN (SELECT telemetry_id FROM telemetry ORDER BY random() LIMIT 30);

INSERT INTO well_targets (well_id, target_date, daily_oil_tons)
SELECT well_id, prod_date, COALESCE(oil_tons, 0)
FROM production
WHERE oil_tons IS NOT NULL;

INSERT INTO pump_sensors (pump_id, ts, vibration_mm_s, temperature_c, current_a, rpm)
SELECT
    p.pump_id,
    ts,
    ROUND(
        (2.0 + random()*0.5
         + GREATEST(0, EXTRACT(EPOCH FROM (ts - '2025-01-01'::timestamp))/86400/60 * p.pump_id * 0.3)
        )::numeric, 3) AS vibration_mm_s,
    ROUND((random()*15 + 55)::numeric, 2) AS temperature_c,
    ROUND((random()*5 + 40)::numeric, 2)  AS current_a,
    (1450 + (random()*50)::int)           AS rpm
FROM (VALUES (1),(2),(3),(4),(5)) AS p(pump_id)
CROSS JOIN generate_series(
    '2025-01-01 00:00'::timestamp,
    '2025-03-01 23:00'::timestamp,
    '1 hour'::interval
) ts;

UPDATE pump_sensors SET vibration_mm_s = vibration_mm_s * 4
WHERE sensor_id IN (SELECT sensor_id FROM pump_sensors ORDER BY random() LIMIT 25);

INSERT INTO pump_failures (pump_id, failure_ts, failure_type) VALUES
    (1, '2025-02-15 14:30', 'bearing'),
    (2, '2025-02-22 09:10', 'overheat'),
    (3, '2025-02-28 18:45', 'vibration'),
    (4, '2025-02-10 03:20', 'electrical'),
    (5, '2025-02-25 22:00', 'bearing');

INSERT INTO deliveries (delivery_date, route_from, route_to, distance_km, volume_tons, cost_rub, delay_hours, weather, driver)
SELECT
    ('2025-01-01'::date + (random()*89)::int) AS delivery_date,
    (ARRAY['Самотлор','Приобск','Ванкор','Уренгой','Ромашкино'])[1 + (random()*4)::int]      AS route_from,
    (ARRAY['Москва','Санкт-Петербург','Казань','Новосибирск','Краснодар','Уфа'])[1 + (random()*5)::int] AS route_to,
    ROUND((random()*3000 + 500)::numeric, 2)         AS distance_km,
    ROUND((random()*40 + 10)::numeric, 2)            AS volume_tons,
    ROUND((random()*200000 + 50000)::numeric, 2)     AS cost_rub,
    CASE
        WHEN random() < 0.6 THEN 0
        WHEN random() < 0.85 THEN ROUND((random()*4)::numeric, 2)
        ELSE ROUND((random()*20 + 4)::numeric, 2)
    END AS delay_hours,
    (ARRAY['clear','rain','snow','fog','storm'])[1 + (random()*4)::int] AS weather,
    (ARRAY['Иванов','Петров','Сидоров','Кузнецов','Смирнов','Попов'])[1 + (random()*5)::int] AS driver
FROM generate_series(1, 500);

UPDATE deliveries
SET delay_hours = delay_hours + ROUND((random()*8 + 2)::numeric, 2)
WHERE weather IN ('storm', 'snow') AND random() < 0.7;

SELECT 'wells' AS table_name, COUNT(*) AS rows FROM wells
UNION ALL SELECT 'production', COUNT(*) FROM production
UNION ALL SELECT 'telemetry',  COUNT(*) FROM telemetry
UNION ALL SELECT 'well_targets', COUNT(*) FROM well_targets
UNION ALL SELECT 'pump_sensors', COUNT(*) FROM pump_sensors
UNION ALL SELECT 'pump_failures', COUNT(*) FROM pump_failures
UNION ALL SELECT 'deliveries',  COUNT(*) FROM deliveries;
