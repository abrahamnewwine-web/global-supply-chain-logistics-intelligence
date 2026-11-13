"""Automated verification suite for Global Supply Chain & Logistics Intelligence."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from src.analytics import FilterParams, get_dashboard_data
from src.ba_artifacts import generate_all_ba_artifacts
from src.config import DB_PATH, DOCS_BA_DIR
from src.pipeline import run_pipeline

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_warehouse() -> None:
    run_pipeline()
    generate_all_ba_artifacts()


def test_etl_integrity() -> None:
    assert DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM fact_shipments").fetchone()[0]
        assert cnt == 5000
        orphans = conn.execute(
            "SELECT COUNT(*) FROM fact_shipments s LEFT JOIN dim_route r ON s.route_id = r.route_id WHERE r.route_id IS NULL"
        ).fetchone()[0]
        assert orphans == 0


def test_kpi_reconciliation() -> None:
    k = get_dashboard_data(FilterParams())["kpis"]
    assert k["total_shipments"] == 5000
    assert pytest.approx(k["disruption_rate_pct"] + k["success_rate_pct"], abs=0.02) == 100.0
    assert k["disruption_rate_pct"] == 61.26
    assert k["success_rate_pct"] == 38.74
    assert 19.0 <= k["avg_lead_time_days"] <= 19.7
    assert k["high_risk_rate_pct"] == 31.42
    assert 4.5 <= k["avg_risk_index"] <= 4.7
    assert 2.80 <= k["avg_fuel_price_usd"] <= 2.90


def test_weather_disruption_sum() -> None:
    d = get_dashboard_data(FilterParams())
    assert d["by_weather"][0]["weather_condition"] == "Hurricane"
    assert sum(w["disrupted_shipments"] for w in d["by_weather"]) == d["kpis"]["disrupted_shipments"]


def test_dimension_sums() -> None:
    d = get_dashboard_data(FilterParams())
    assert sum(m["shipment_volume"] for m in d["by_transport_mode"]) == 5000
    assert sum(c["shipment_volume"] for c in d["by_product_category"]) == 5000
    assert sum(r["total_shipments"] for r in d["by_region"]) == 5000


def test_critical_route_spotlight() -> None:
    d = get_dashboard_data(FilterParams())
    assert d["critical_route"]["route_name"].startswith("Rotterdam")


def test_api_and_export() -> None:
    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/api/dashboard?transport_mode=Sea").status_code == 200
    assert client.get("/api/dashboard?transport_mode=Teleport").status_code == 400
    csv_res = client.get("/api/export/routes-csv")
    assert csv_res.status_code == 200
    assert "route_name" in csv_res.text
    assert (DOCS_BA_DIR / "rtm_workbook.xlsx").exists()
    assert (DOCS_BA_DIR / "uat_test_log.xlsx").exists()
    assert (DOCS_BA_DIR / "executive_insights_report.pdf").exists()
