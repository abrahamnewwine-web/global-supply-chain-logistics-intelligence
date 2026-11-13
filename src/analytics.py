"""Analytical query and route-risk scoring engine for Global Supply Chain."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.config import DB_PATH


@dataclass(frozen=True)
class FilterParams:
    """Interactive logistics dashboard filter parameters."""

    year: int | None = None
    quarter: int | None = None
    month: int | None = None
    origin_port: str | None = None
    transport_mode: str | None = None
    product_category: str | None = None
    weather_condition: str | None = None


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        from src.pipeline import run_pipeline

        run_pipeline()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _build_where(filters: FilterParams) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.year is not None:
        clauses.append("d.year = ?")
        params.append(filters.year)
    if filters.quarter is not None:
        clauses.append("d.quarter = ?")
        params.append(filters.quarter)
    if filters.month is not None:
        clauses.append("d.month_num = ?")
        params.append(filters.month)
    if filters.origin_port and filters.origin_port != "All":
        clauses.append("r.origin_port = ?")
        params.append(filters.origin_port)
    if filters.transport_mode and filters.transport_mode != "All":
        clauses.append("car.transport_mode = ?")
        params.append(filters.transport_mode)
    if filters.product_category and filters.product_category != "All":
        clauses.append("cat.category_name = ?")
        params.append(filters.product_category)
    if filters.weather_condition and filters.weather_condition != "All":
        clauses.append("w.weather_condition = ?")
        params.append(filters.weather_condition)
    return (f"WHERE {' AND '.join(clauses)}" if clauses else ""), params


def get_filter_options() -> dict[str, list[Any]]:
    """Return valid slicer dropdown options."""
    with _connect() as conn:
        return {
            "years": [r[0] for r in conn.execute("SELECT DISTINCT year FROM dim_date ORDER BY year")],
            "quarters": [1, 2, 3, 4],
            "months": [
                {"month_num": r[0], "month_name": r[1]}
                for r in conn.execute("SELECT DISTINCT month_num, month_name FROM dim_date ORDER BY month_num")
            ],
            "origin_ports": [r[0] for r in conn.execute("SELECT DISTINCT origin_port FROM dim_route ORDER BY origin_port")],
            "transport_modes": [r[0] for r in conn.execute("SELECT DISTINCT transport_mode FROM dim_carrier ORDER BY transport_mode")],
            "product_categories": [r[0] for r in conn.execute("SELECT category_name FROM dim_product_category ORDER BY category_name")],
            "weather_conditions": [r[0] for r in conn.execute("SELECT weather_condition FROM dim_weather ORDER BY severity_tier DESC")],
        }


def get_dashboard_data(filters: FilterParams) -> dict[str, Any]:
    """Compute reconciled supply chain KPIs, trends, breakdowns, and critical routes."""
    where_sql, params = _build_where(filters)
    joins = """
        FROM fact_shipments s
        JOIN dim_date d ON s.date_key = d.date_key
        JOIN dim_route r ON s.route_id = r.route_id
        JOIN dim_carrier car ON s.carrier_id = car.carrier_id
        JOIN dim_product_category cat ON s.category_id = cat.category_id
        JOIN dim_weather w ON s.weather_id = w.weather_id
    """

    with _connect() as conn:
        kpi_sql = f"""
            SELECT
                COUNT(*) AS total_shipments,
                COALESCE(SUM(s.disrupted_flag), 0) AS disrupted_shipments,
                COALESCE(SUM(CASE WHEN s.disrupted_flag = 0 THEN 1 ELSE 0 END), 0) AS successful_shipments,
                COALESCE(AVG(s.lead_time_days), 0.0) AS avg_lead_time_days,
                COALESCE(SUM(s.carrier_reliable_flag), 0) AS reliable_shipments,
                COALESCE(AVG(s.risk_index), 0.0) AS avg_risk_index,
                COALESCE(SUM(s.high_risk_flag), 0) AS high_risk_shipments,
                COALESCE(AVG(s.fuel_price_usd), 0.0) AS avg_fuel_price_usd
            {joins}
            {where_sql}
        """
        k_row = dict(conn.execute(kpi_sql, params).fetchone())

        monthly_df = pd.read_sql_query(
            f"""
            SELECT
                d.year_month,
                COUNT(*) AS total_shipments,
                SUM(s.disrupted_flag) AS disrupted_shipments,
                ROUND(100.0 * SUM(s.disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct,
                ROUND(AVG(s.lead_time_days), 2) AS avg_lead_time_days,
                ROUND(AVG(s.risk_index), 2) AS avg_risk_index,
                ROUND(AVG(s.fuel_price_usd), 2) AS avg_fuel_price_usd,
                SUM(s.carrier_reliable_flag) AS reliable_shipments
            {joins}
            {where_sql}
            GROUP BY d.year_month
            ORDER BY d.year_month
            """,
            conn,
            params=params,
        )

        mode_df = pd.read_sql_query(
            f"""
            SELECT car.transport_mode, COUNT(*) AS shipment_volume,
                   ROUND(AVG(s.lead_time_days), 2) AS avg_lead_time_days
            {joins} {where_sql}
            GROUP BY car.transport_mode ORDER BY shipment_volume DESC
            """,
            conn,
            params=params,
        )

        category_df = pd.read_sql_query(
            f"""
            SELECT cat.category_name, COUNT(*) AS shipment_volume
            {joins} {where_sql}
            GROUP BY cat.category_name ORDER BY shipment_volume DESC
            """,
            conn,
            params=params,
        )

        weather_df = pd.read_sql_query(
            f"""
            SELECT w.weather_condition,
                   COUNT(*) AS total_shipments,
                   SUM(s.disrupted_flag) AS disrupted_shipments
            {joins} {where_sql}
            GROUP BY w.weather_id, w.weather_condition
            ORDER BY disrupted_shipments DESC
            """,
            conn,
            params=params,
        )

        region_df = pd.read_sql_query(
            f"""
            SELECT r.region, COUNT(*) AS total_shipments
            {joins} {where_sql}
            GROUP BY r.region ORDER BY total_shipments DESC
            """,
            conn,
            params=params,
        )

        routes_df = pd.read_sql_query(
            f"""
            SELECT
                r.route_name,
                r.region,
                COUNT(*) AS total_shipments,
                ROUND(AVG(s.risk_index), 2) AS avg_risk_index,
                ROUND(AVG(s.lead_time_days), 2) AS avg_lead_time_days,
                ROUND(100.0 * SUM(s.disrupted_flag) / COUNT(*), 2) AS disruption_rate_pct,
                ROUND(100.0 * SUM(s.high_risk_flag) / COUNT(*), 2) AS high_risk_rate_pct
            {joins} {where_sql}
            GROUP BY r.route_id, r.route_name, r.region
            ORDER BY avg_risk_index DESC, avg_lead_time_days DESC
            """,
            conn,
            params=params,
        )

    tot = int(k_row["total_shipments"] or 0)
    dis = int(k_row["disrupted_shipments"] or 0)
    suc = int(k_row["successful_shipments"] or 0)
    hr = int(k_row["high_risk_shipments"] or 0)

    disruption_rate = round(100.0 * dis / tot, 2) if tot > 0 else 0.0
    success_rate = round(100.0 * suc / tot, 2) if tot > 0 else 0.0
    high_risk_rate = round(100.0 * hr / tot, 2) if tot > 0 else 0.0
    carrier_reliability_pct = round(100.0 * int(k_row["reliable_shipments"] or 0) / tot, 2) if tot > 0 else 0.0

    # Month-over-Month deltas
    vol_mom = 0.0
    dis_mom = 0.0
    if len(monthly_df) >= 2:
        p_vol = float(monthly_df.iloc[-2]["total_shipments"])
        c_vol = float(monthly_df.iloc[-1]["total_shipments"])
        vol_mom = round(((c_vol - p_vol) / p_vol * 100.0) if p_vol else 0.0, 2)
        dis_mom = round(float(monthly_df.iloc[-1]["disruption_rate_pct"]) - float(monthly_df.iloc[-2]["disruption_rate_pct"]), 2)

    critical_route = routes_df.iloc[0].to_dict() if not routes_df.empty else None

    return {
        "filters": {
            "year": filters.year,
            "quarter": filters.quarter,
            "month": filters.month,
            "origin_port": filters.origin_port or "All",
            "transport_mode": filters.transport_mode or "All",
            "product_category": filters.product_category or "All",
            "weather_condition": filters.weather_condition or "All",
        },
        "kpis": {
            "total_shipments": tot,
            "disrupted_shipments": dis,
            "successful_shipments": suc,
            "disruption_rate_pct": disruption_rate,
            "success_rate_pct": success_rate,
            "avg_lead_time_days": round(float(k_row["avg_lead_time_days"] or 0.0), 2),
            "reliable_shipments": int(k_row["reliable_shipments"] or 0),
            "carrier_reliability_pct": carrier_reliability_pct,
            "avg_risk_index": round(float(k_row["avg_risk_index"] or 0.0), 2),
            "high_risk_shipments": hr,
            "high_risk_rate_pct": high_risk_rate,
            "avg_fuel_price_usd": round(float(k_row["avg_fuel_price_usd"] or 0.0), 2),
            "volume_mom_pct": vol_mom,
            "disruption_mom_pp": dis_mom,
        },
        "critical_route": critical_route,
        "monthly_trends": monthly_df.to_dict(orient="records"),
        "by_transport_mode": mode_df.to_dict(orient="records"),
        "by_product_category": category_df.to_dict(orient="records"),
        "by_weather": weather_df.to_dict(orient="records"),
        "by_region": region_df.to_dict(orient="records"),
        "top_routes": routes_df.head(12).to_dict(orient="records"),
    }
