-- Global Supply Chain & Logistics Intelligence - Production SQL Queries

-- 1. Executive Logistics KPI Summary
SELECT
    COUNT(*) AS total_shipments,
    SUM(disrupted_flag) AS disrupted_shipments,
    ROUND(100.0 * SUM(disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN disrupted_flag = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(AVG(lead_time_days), 2) AS avg_lead_time_days,
    SUM(carrier_reliable_flag) AS reliable_shipments,
    ROUND(AVG(risk_index), 2) AS avg_risk_index,
    ROUND(100.0 * SUM(high_risk_flag) / COUNT(*), 2) AS high_risk_rate_pct,
    ROUND(AVG(fuel_price_usd), 2) AS avg_fuel_price_usd
FROM fact_shipments;

-- 2. Route Risk & Critical Corridor Ranking
SELECT
    r.route_name,
    r.origin_port,
    r.destination_port,
    r.region,
    COUNT(*) AS total_shipments,
    ROUND(AVG(s.risk_index), 2) AS avg_risk_index,
    ROUND(AVG(s.lead_time_days), 2) AS avg_lead_time_days,
    ROUND(100.0 * SUM(s.disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct,
    ROUND(100.0 * SUM(s.high_risk_flag) / COUNT(*), 2) AS high_risk_rate_pct
FROM fact_shipments s
JOIN dim_route r ON s.route_id = r.route_id
GROUP BY r.route_id, r.route_name, r.origin_port, r.destination_port, r.region
ORDER BY avg_risk_index DESC, avg_lead_time_days DESC
LIMIT 15;

-- 3. Disruptions by Weather Condition
SELECT
    w.weather_condition,
    COUNT(*) AS total_shipments,
    SUM(s.disrupted_flag) AS disrupted_shipments,
    ROUND(100.0 * SUM(s.disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct
FROM fact_shipments s
JOIN dim_weather w ON s.weather_id = w.weather_id
GROUP BY w.weather_id, w.weather_condition
ORDER BY disrupted_shipments DESC;

-- 4. Monthly Volume & Disruption Trend
SELECT
    d.year_month,
    COUNT(*) AS shipment_volume,
    ROUND(100.0 * SUM(s.disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct,
    ROUND(AVG(s.lead_time_days), 2) AS avg_lead_time_days
FROM fact_shipments s
JOIN dim_date d ON s.date_key = d.date_key
GROUP BY d.year_month
ORDER BY d.year_month;
