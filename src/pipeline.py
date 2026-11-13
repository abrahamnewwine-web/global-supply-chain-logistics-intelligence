"""ETL pipeline for Global Supply Chain & Logistics Intelligence.

Generates a calibrated 5,000-shipment multi-modal global logistics benchmark
dataset (2024-2025), builds the relational star schema, exports CSVs, and
loads the SQLite analytics warehouse.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    CARRIERS,
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DB_PATH,
    PRODUCT_CATEGORIES,
    RANDOM_SEED,
    ROUTES,
    SQL_DIR,
    WEATHER_CONDITIONS,
)


def build_dim_date() -> pd.DataFrame:
    """Create daily calendar dimension across 2024-2025."""
    dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    return pd.DataFrame(
        {
            "date_key": dates.strftime("%Y%m%d").astype(int),
            "full_date": dates.strftime("%Y-%m-%d"),
            "year": dates.year,
            "quarter": dates.quarter,
            "quarter_label": "Q" + dates.quarter.astype(str),
            "month_num": dates.month,
            "month_name": dates.strftime("%B"),
            "year_month": dates.strftime("%Y-%m"),
        }
    )


def generate_supply_chain_data(seed: int = RANDOM_SEED) -> dict[str, pd.DataFrame]:
    """Generate calibrated 5,000-shipment star schema tables."""
    rng = np.random.default_rng(seed)
    dim_date = build_dim_date()
    dim_category = pd.DataFrame(
        PRODUCT_CATEGORIES, columns=["category_id", "category_name", "temp_sensitive"]
    )
    dim_weather = pd.DataFrame(
        WEATHER_CONDITIONS, columns=["weather_id", "weather_condition", "severity_tier"]
    )
    dim_carrier = pd.DataFrame(
        CARRIERS, columns=["carrier_id", "carrier_name", "transport_mode"]
    )
    dim_route = pd.DataFrame(
        [r[:6] for r in ROUTES],
        columns=[
            "route_id",
            "route_name",
            "origin_port",
            "destination_port",
            "region",
            "distance_km",
        ],
    )

    # Exact target route counts summing to 5,000
    route_ids: list[int] = []
    route_base_risk: list[float] = []
    route_base_lead: list[float] = []
    for r in ROUTES:
        rid, _, _, _, _, _, cnt, r_risk, r_lead = r
        route_ids.extend([rid] * cnt)
        route_base_risk.extend([r_risk] * cnt)
        route_base_lead.extend([r_lead] * cnt)

    n = len(route_ids)
    assert n == 5000, f"Expected 5000 shipments, got {n}"

    perm = rng.permutation(n)
    route_ids_arr = np.array(route_ids)[perm]
    base_risk_arr = np.array(route_base_risk)[perm]
    base_lead_arr = np.array(route_base_lead)[perm]

    # Exact weather disruptions matching spec proportions: 990 + 797 + 498 + 410 + 368 = 3063 (61.26%)
    weather_spec = [
        (1, 990, 1280),  # Hurricane
        (2, 797, 1140),  # Storm
        (3, 498, 860),   # Fog
        (4, 410, 860),   # Rain
        (5, 368, 860),   # Clear
    ]
    w_ids: list[int] = []
    disrupted_list: list[int] = []
    for wid, dis_cnt, tot_cnt in weather_spec:
        w_ids.extend([wid] * tot_cnt)
        disrupted_list.extend([1] * dis_cnt + [0] * (tot_cnt - dis_cnt))
    w_perm = rng.permutation(n)
    weather_arr = np.array(w_ids)[w_perm]
    disrupted_arr = np.array(disrupted_list)[w_perm]

    # High-risk shipment flag: exact 1,571 high-risk shipments (31.42%)
    # Assign risk scores calibrated so avg risk ~ 4.61 and exactly 1,571 are >= 5.25
    high_risk_arr = np.zeros(n, dtype=int)
    high_risk_idx = rng.choice(n, size=1571, replace=False)
    high_risk_arr[high_risk_idx] = 1

    risk_scores = np.where(
        high_risk_arr == 1,
        np.clip(base_risk_arr + rng.uniform(0.65, 2.25, size=n), 5.25, 9.80),
        np.clip(base_risk_arr - rng.uniform(0.10, 1.55, size=n), 1.20, 5.20),
    )
    # Shift non-high-risk slightly if needed so overall mean lands cleanly at ~4.61
    current_mean = float(np.mean(risk_scores))
    risk_scores = np.clip(risk_scores + (4.61 - current_mean), 1.0, 9.9)
    # Re-ensure high_risk_flag strictly aligns with risk_index >= threshold
    threshold = float(np.quantile(risk_scores, 1.0 - 1571 / n))
    high_risk_arr = (risk_scores >= threshold).astype(int)

    # Carrier assignments balanced across modes (Air/Sea ~1.3K each, Road/Rail ~1.2K each)
    mode_probs = np.array([0.13, 0.13, 0.13, 0.13, 0.12, 0.12, 0.12, 0.12])
    carrier_arr = rng.choice(dim_carrier["carrier_id"].to_numpy(), size=n, p=mode_probs)

    # Product category assignments ~1,000 each
    category_arr = rng.choice(dim_category["category_id"].to_numpy(), size=n)

    # Carrier reliability: ~3,770 reliable shipments (3.77K)
    reliable_arr = np.zeros(n, dtype=int)
    reliable_arr[rng.choice(n, size=3770, replace=False)] = 1

    # Date assignment across 24 months (2024-01 .. 2025-12) with realistic volume rhythm
    months = sorted(dim_date["year_month"].unique())
    month_weights = np.array(
        [
            0.035, 0.041, 0.045, 0.042, 0.042, 0.036, 0.039, 0.042, 0.041, 0.044, 0.039, 0.044,
            0.039, 0.043, 0.042, 0.042, 0.040, 0.038, 0.044, 0.046, 0.045, 0.046, 0.045, 0.044,
        ]
    )
    month_weights /= month_weights.sum()
    chosen_months = rng.choice(months, size=n, p=month_weights)
    month_to_dates = {
        ym: dim_date.loc[dim_date["year_month"] == ym, "date_key"].to_numpy()
        for ym in months
    }
    date_keys = np.array([int(rng.choice(month_to_dates[ym])) for ym in chosen_months])

    # Lead time: calibrated around route baseline + disruption penalty so mean ~ 19.36 days
    lead_times = base_lead_arr + np.where(disrupted_arr == 1, rng.normal(1.3, 1.8, n), rng.normal(-1.4, 1.5, n))
    lead_times = np.clip(lead_times, 3.0, 48.0)
    # Center non-Rotterdam routes gently to preserve Rotterdam->Marseille ~27.76 and global mean ~19.36
    non_rot_mask = route_ids_arr != 1
    diff_needed = (19.36 - float(np.mean(lead_times))) * (n / non_rot_mask.sum())
    lead_times[non_rot_mask] = np.clip(lead_times[non_rot_mask] + diff_needed, 3.0, 48.0)

    fuel_prices = np.clip(rng.normal(2.85, 0.28, size=n), 2.05, 3.95)
    fuel_prices = np.round(fuel_prices + (2.85 - float(np.mean(fuel_prices))), 2)

    shipment_values = np.round(rng.lognormal(mean=10.5, sigma=0.45, size=n), 2)

    fact_shipments = pd.DataFrame(
        {
            "shipment_id": np.arange(1, n + 1),
            "date_key": date_keys,
            "route_id": route_ids_arr,
            "carrier_id": carrier_arr,
            "category_id": category_arr,
            "weather_id": weather_arr,
            "disrupted_flag": disrupted_arr,
            "carrier_reliable_flag": reliable_arr,
            "high_risk_flag": high_risk_arr,
            "lead_time_days": np.round(lead_times, 2),
            "risk_index": np.round(risk_scores, 2),
            "fuel_price_usd": fuel_prices,
            "shipment_value_usd": shipment_values,
        }
    )

    return {
        "dim_date": dim_date,
        "dim_product_category": dim_category,
        "dim_route": dim_route,
        "dim_carrier": dim_carrier,
        "dim_weather": dim_weather,
        "fact_shipments": fact_shipments,
    }


def export_csvs(tables: dict[str, pd.DataFrame]) -> None:
    """Persist processed CSV files."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(DATA_PROCESSED_DIR / f"{name}.csv", index=False)


def load_sqlite(tables: dict[str, pd.DataFrame], db_path: Path = DB_PATH) -> None:
    """Create schema and load supply chain warehouse into SQLite."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    schema_sql = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    load_order = [
        "dim_date",
        "dim_product_category",
        "dim_route",
        "dim_carrier",
        "dim_weather",
        "fact_shipments",
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        for tbl in load_order:
            tables[tbl].to_sql(tbl, conn, if_exists="append", index=False, chunksize=2000)
        conn.commit()


def run_pipeline() -> dict[str, int]:
    """Run full Supply Chain ETL pipeline."""
    tables = generate_supply_chain_data()
    export_csvs(tables)
    load_sqlite(tables)
    return {name: len(df) for name, df in tables.items()}


if __name__ == "__main__":
    print("ETL completed:", run_pipeline())
