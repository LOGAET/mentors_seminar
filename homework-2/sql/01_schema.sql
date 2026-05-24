CREATE SCHEMA IF NOT EXISTS oilfield;
SET search_path TO oilfield, public;

CREATE TABLE IF NOT EXISTS wells (
    well_id        SERIAL PRIMARY KEY,
    well_name      VARCHAR(50) NOT NULL UNIQUE,
    field_name     VARCHAR(100) NOT NULL,
    region         VARCHAR(100) NOT NULL,
    well_type      VARCHAR(20) NOT NULL CHECK (well_type IN ('oil','gas','mixed')),
    drill_date     DATE NOT NULL,
    depth_m        NUMERIC(8,2) NOT NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS production (
    production_id  BIGSERIAL PRIMARY KEY,
    well_id        INT NOT NULL REFERENCES wells(well_id),
    prod_date      DATE NOT NULL,
    oil_tons       NUMERIC(10,2),
    gas_m3         NUMERIC(12,2),
    water_tons     NUMERIC(10,2),
    downtime_hours NUMERIC(5,2) DEFAULT 0,
    UNIQUE(well_id, prod_date)
);
CREATE INDEX IF NOT EXISTS idx_production_date ON production(prod_date);
CREATE INDEX IF NOT EXISTS idx_production_well ON production(well_id);

CREATE TABLE IF NOT EXISTS telemetry (
    telemetry_id   BIGSERIAL PRIMARY KEY,
    well_id        INT NOT NULL REFERENCES wells(well_id),
    ts             TIMESTAMP NOT NULL,
    pressure_bar   NUMERIC(8,2),
    temperature_c  NUMERIC(6,2),
    power_kw       NUMERIC(8,2),
    pump_hours     NUMERIC(5,2),
    UNIQUE(well_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(ts);
CREATE INDEX IF NOT EXISTS idx_telemetry_well ON telemetry(well_id);

CREATE TABLE IF NOT EXISTS well_targets (
    target_id      BIGSERIAL PRIMARY KEY,
    well_id        INT NOT NULL REFERENCES wells(well_id),
    target_date    DATE NOT NULL,
    daily_oil_tons NUMERIC(10,2) NOT NULL,
    UNIQUE(well_id, target_date)
);

CREATE TABLE IF NOT EXISTS pump_sensors (
    sensor_id      BIGSERIAL PRIMARY KEY,
    pump_id        INT NOT NULL,
    ts             TIMESTAMP NOT NULL,
    vibration_mm_s NUMERIC(6,3),
    temperature_c  NUMERIC(6,2),
    current_a      NUMERIC(6,2),
    rpm            INT,
    UNIQUE(pump_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_pump_ts ON pump_sensors(ts);

CREATE TABLE IF NOT EXISTS pump_failures (
    failure_id     BIGSERIAL PRIMARY KEY,
    pump_id        INT NOT NULL,
    failure_ts     TIMESTAMP NOT NULL,
    failure_type   VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id    BIGSERIAL PRIMARY KEY,
    delivery_date  DATE NOT NULL,
    route_from     VARCHAR(100) NOT NULL,
    route_to       VARCHAR(100) NOT NULL,
    distance_km    NUMERIC(8,2) NOT NULL,
    volume_tons    NUMERIC(10,2) NOT NULL,
    cost_rub       NUMERIC(12,2) NOT NULL,
    delay_hours    NUMERIC(5,2) DEFAULT 0,
    weather        VARCHAR(20) NOT NULL,
    driver         VARCHAR(50) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_deliveries_date ON deliveries(delivery_date);
