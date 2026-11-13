"""Configuration and domain catalog for Global Supply Chain & Logistics Intelligence."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
DOCS_BA_DIR = BASE_DIR / "docs" / "business-analysis"
SCREENSHOTS_DIR = BASE_DIR / "assets" / "screenshots"
DB_PATH = DATA_PROCESSED_DIR / "supply_chain.db"

RANDOM_SEED = 20250202

PRODUCT_CATEGORIES = [
    (1, "Electronics", 0),
    (2, "Textiles", 0),
    (3, "Perishables", 1),
    (4, "Pharmaceuticals", 1),
    (5, "Automotive", 0),
]

WEATHER_CONDITIONS = [
    (1, "Hurricane", 5),
    (2, "Storm", 4),
    (3, "Fog", 3),
    (4, "Rain", 2),
    (5, "Clear", 1),
]

CARRIERS = [
    (1, "SkyFreight Global", "Air"),
    (2, "AeroCargo Express", "Air"),
    (3, "Oceanic Maersk Line", "Sea"),
    (4, "Pacific Container Corp", "Sea"),
    (5, "EuroHaul Logistics", "Road"),
    (6, "TransContinental Trucking", "Road"),
    (7, "Eurasia Rail Freight", "Rail"),
    (8, "NorthStar Intermodal", "Rail"),
]

ROUTES = [
    (1, "Rotterdam → Marseille", "Rotterdam", "Marseille", "Europe", 1250, 80, 5.45, 27.76),
    (2, "Antwerp → Busan", "Antwerp", "Busan", "Asia", 18400, 101, 4.56, 16.22),
    (3, "Antwerp → Dubai", "Antwerp", "Dubai", "Asia", 11200, 80, 4.73, 17.36),
    (4, "Antwerp → Hamburg", "Antwerp", "Hamburg", "Europe", 520, 70, 4.72, 19.02),
    (5, "Antwerp → Los Angeles", "Antwerp", "Los Angeles", "North America", 14800, 57, 4.58, 17.50),
    (6, "Shanghai → Rotterdam", "Shanghai", "Rotterdam", "Asia", 19500, 260, 4.82, 22.40),
    (7, "Singapore → Hamburg", "Singapore", "Hamburg", "Asia", 15900, 250, 4.65, 20.80),
    (8, "Busan → Los Angeles", "Busan", "Los Angeles", "Asia", 9650, 230, 4.55, 18.70),
    (9, "Shanghai → Singapore", "Shanghai", "Singapore", "Asia", 4100, 290, 4.42, 15.60),
    (10, "Singapore → Dubai", "Singapore", "Dubai", "Asia", 6500, 270, 4.60, 17.10),
    (11, "Dubai → Rotterdam", "Dubai", "Rotterdam", "Asia", 11400, 240, 4.68, 19.80),
    (12, "Busan → Shanghai", "Busan", "Shanghai", "Asia", 850, 280, 4.35, 14.20),
    (13, "Rotterdam → Hamburg", "Rotterdam", "Hamburg", "Europe", 490, 310, 4.52, 16.40),
    (14, "Hamburg → Marseille", "Hamburg", "Marseille", "Europe", 1320, 280, 4.66, 20.10),
    (15, "Rotterdam → Antwerp", "Rotterdam", "Antwerp", "Europe", 120, 290, 4.44, 15.80),
    (16, "Marseille → Antwerp", "Marseille", "Antwerp", "Europe", 1020, 270, 4.71, 21.30),
    (17, "Hamburg → Antwerp", "Hamburg", "Antwerp", "Europe", 520, 260, 4.58, 18.60),
    (18, "Marseille → Rotterdam", "Marseille", "Rotterdam", "Europe", 1250, 290, 4.78, 22.90),
    (19, "Los Angeles → Rotterdam", "Los Angeles", "Rotterdam", "North America", 14800, 275, 4.62, 21.50),
    (20, "Los Angeles → Shanghai", "Los Angeles", "Shanghai", "North America", 10500, 270, 4.54, 19.40),
    (21, "Dubai → Durban", "Dubai", "Durban", "Other", 7100, 300, 4.69, 20.90),
    (22, "Marseille → Santos", "Marseille", "Santos", "Other", 9500, 247, 4.57, 21.60),
]
