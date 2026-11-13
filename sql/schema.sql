-- Global Supply Chain & Logistics Intelligence - Star Schema DDL (SQLite)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_shipments;
DROP TABLE IF EXISTS dim_weather;
DROP TABLE IF EXISTS dim_carrier;
DROP TABLE IF EXISTS dim_route;
DROP TABLE IF EXISTS dim_product_category;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,
    full_date       TEXT NOT NULL,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    quarter_label   TEXT NOT NULL,
    month_num       INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    year_month      TEXT NOT NULL
);

CREATE TABLE dim_product_category (
    category_id     INTEGER PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE,
    temp_sensitive  INTEGER NOT NULL CHECK (temp_sensitive IN (0, 1))
);

CREATE TABLE dim_route (
    route_id        INTEGER PRIMARY KEY,
    route_name      TEXT NOT NULL UNIQUE,
    origin_port     TEXT NOT NULL,
    destination_port TEXT NOT NULL,
    region          TEXT NOT NULL,
    distance_km     INTEGER NOT NULL
);

CREATE TABLE dim_carrier (
    carrier_id      INTEGER PRIMARY KEY,
    carrier_name    TEXT NOT NULL UNIQUE,
    transport_mode  TEXT NOT NULL CHECK (transport_mode IN ('Air', 'Sea', 'Road', 'Rail'))
);

CREATE TABLE dim_weather (
    weather_id      INTEGER PRIMARY KEY,
    weather_condition TEXT NOT NULL UNIQUE,
    severity_tier   INTEGER NOT NULL
);

CREATE TABLE fact_shipments (
    shipment_id     INTEGER PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    route_id        INTEGER NOT NULL REFERENCES dim_route(route_id),
    carrier_id      INTEGER NOT NULL REFERENCES dim_carrier(carrier_id),
    category_id     INTEGER NOT NULL REFERENCES dim_product_category(category_id),
    weather_id      INTEGER NOT NULL REFERENCES dim_weather(weather_id),
    disrupted_flag  INTEGER NOT NULL CHECK (disrupted_flag IN (0, 1)),
    carrier_reliable_flag INTEGER NOT NULL CHECK (carrier_reliable_flag IN (0, 1)),
    high_risk_flag  INTEGER NOT NULL CHECK (high_risk_flag IN (0, 1)),
    lead_time_days  REAL NOT NULL CHECK (lead_time_days > 0),
    risk_index      REAL NOT NULL CHECK (risk_index BETWEEN 0 AND 10),
    fuel_price_usd  REAL NOT NULL CHECK (fuel_price_usd > 0),
    shipment_value_usd REAL NOT NULL CHECK (shipment_value_usd > 0)
);

CREATE INDEX idx_shipments_date ON fact_shipments(date_key);
CREATE INDEX idx_shipments_route ON fact_shipments(route_id, disrupted_flag);
CREATE INDEX idx_shipments_weather ON fact_shipments(weather_id, disrupted_flag);
CREATE INDEX idx_shipments_carrier ON fact_shipments(carrier_id, category_id);
