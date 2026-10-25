"""Shared paths and settings for the KPI reporting pipeline.

Everything is resolved from the repository root, so the pipeline runs
from any working directory as long as it is launched as
``python src/pipeline.py`` from the repo root or imported from ``src``.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
LOG_DIR = ROOT / "logs"
DB_PATH = ROOT / "data" / "olist.db"

# Kaggle file name -> SQLite table name. The geolocation table is loaded
# for completeness (it is one of the 9 Olist tables) but is NOT joined
# into master_orders: it has one row per zip-code prefix, not per order,
# so joining it would fan out the order grain. Customer state/city
# already give the map breakdown the dashboard needs.
TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

SQL_FILES_IN_ORDER = [
    "01_clean_orders.sql",
    "02_master_table.sql",
    "03_kpi_monthly.sql",
]
