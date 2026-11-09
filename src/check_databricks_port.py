"""Check the Databricks SQL port against the SQLite pipeline's numbers.

Usage, from the repository root:
    pip install duckdb sqlglot
    python src/check_databricks_port.py

This does NOT run anything on Databricks. It transpiles
sql/databricks/01-03 from Spark SQL to DuckDB with sqlglot, runs them
against the raw CSVs, and executes 04_reconcile.sql. It proves the port
is logically equivalent; it does not prove it executes on a Databricks
warehouse. Only a real run recorded in docs/databricks-run.md does that.

Timestamp columns are staged as strings, as they arrive in the CSV.
Spark's 00_load_raw.py casts them to timestamps; the ISO strings sort
and compare identically, which is also how the SQLite original behaves.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402
import pandas as pd  # noqa: E402
import sqlglot  # noqa: E402

from config import DATA_RAW, SQL_DIR  # noqa: E402

PORT_DIR = SQL_DIR / "databricks"
TIMESTAMP_COLUMNS = [
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date", "review_creation_date",
    "review_answer_timestamp", "shipping_limit_date",
]
TABLES = {
    "olist_orders_dataset.csv": "orders",
    "olist_customers_dataset.csv": "customers",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}


def run(conn, filename: str):
    sql = (PORT_DIR / filename).read_text(encoding="utf-8")
    return conn.execute(sqlglot.transpile(sql, read="spark", write="duckdb")[0])


def main() -> None:
    conn = duckdb.connect()
    for csv_name, table in TABLES.items():
        df = pd.read_csv(
            DATA_RAW / csv_name,
            dtype={column: str for column in TIMESTAMP_COLUMNS},
        )
        conn.register(f"{table}_df", df)
        conn.execute(f"CREATE TABLE {table} AS SELECT * FROM {table}_df")
    for filename in ["01_clean_orders.sql", "02_master_table.sql", "03_kpi_monthly.sql"]:
        run(conn, filename)
        print(f"Ran {filename} (transpiled to DuckDB)")
    result = run(conn, "04_reconcile.sql").df()
    print(result.to_string(index=False))
    if not (result["result"] == "MATCH").all():
        raise SystemExit("Port does not reconcile with the SQLite pipeline.")


if __name__ == "__main__":
    main()
