"""FastAPI application for Global Supply Chain & Logistics Intelligence."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.analytics import FilterParams, get_dashboard_data, get_filter_options

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Global Supply Chain & Logistics Intelligence",
    description="Interactive executive supply chain risk and disruption BI platform.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"options": get_filter_options()})


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "global-supply-chain-logistics-intelligence"}


@app.get("/api/filters")
def api_filters() -> dict[str, object]:
    return get_filter_options()


@app.get("/api/dashboard")
def api_dashboard(
    year: int | None = Query(default=None, ge=2020, le=2030),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    origin_port: str | None = Query(default=None),
    transport_mode: str | None = Query(default=None),
    product_category: str | None = Query(default=None),
    weather_condition: str | None = Query(default=None),
) -> dict[str, object]:
    opts = get_filter_options()
    checks = [
        (origin_port, opts["origin_ports"], "origin port"),
        (transport_mode, opts["transport_modes"], "transport mode"),
        (product_category, opts["product_categories"], "product category"),
        (weather_condition, opts["weather_conditions"], "weather condition"),
    ]
    for val, valid, label in checks:
        if val and val != "All" and val not in valid:
            raise HTTPException(status_code=400, detail=f"Unknown {label}: {val}")

    params = FilterParams(
        year=year,
        quarter=quarter,
        month=month,
        origin_port=origin_port,
        transport_mode=transport_mode,
        product_category=product_category,
        weather_condition=weather_condition,
    )
    return get_dashboard_data(params)


@app.get("/api/export/routes-csv")
def export_routes_csv(
    year: int | None = Query(default=None, ge=2020, le=2030),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    origin_port: str | None = Query(default=None),
    transport_mode: str | None = Query(default=None),
    product_category: str | None = Query(default=None),
    weather_condition: str | None = Query(default=None),
) -> StreamingResponse:
    data = api_dashboard(
        year=year,
        quarter=quarter,
        month=month,
        origin_port=origin_port,
        transport_mode=transport_mode,
        product_category=product_category,
        weather_condition=weather_condition,
    )
    rows = data["top_routes"]
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("route_name,region,total_shipments,avg_risk_index,avg_lead_time_days,disruption_rate_pct\n")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=supply_chain_routes_risk.csv"},
    )
