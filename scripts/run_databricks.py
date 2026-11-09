"""Execute the KPI SQL port on a real Databricks SQL warehouse.

Required environment:
  DATABRICKS_SERVER_HOSTNAME
  DATABRICKS_HTTP_PATH
  DATABRICKS_TOKEN
  DATABRICKS_CATALOG (default: main)
  DATABRICKS_SCHEMA (default: kpi)
  DATABRICKS_VOLUME (default: raw; Unity Catalog volume name)
  DATABRICKS_VOLUME_ROOT (optional; defaults to /Volumes/<catalog>/<schema>/<volume>)

The nine Olist CSV files must exist in data/raw/. The script stages them
into the configured Unity Catalog volume, creates/replaces source tables,
executes SQL 01-03, and verifies all 11 rows from 04_reconcile.sql.
It writes docs/databricks-run-receipt.json only after a successful run.
Never treat a local DuckDB check as a Databricks execution.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from databricks import sql
from databricks.sdk.errors import DatabricksError

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SQL_DIR = ROOT / "sql" / "databricks"
RECEIPT = ROOT / "docs" / "databricks-run-receipt.json"

FILES = {
    "olist_customers_dataset.csv": ("customers", []),
    "olist_geolocation_dataset.csv": ("geolocation", []),
    "olist_orders_dataset.csv": ("orders", [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]),
    "olist_order_items_dataset.csv": ("order_items", ["shipping_limit_date"]),
    "olist_order_payments_dataset.csv": ("order_payments", []),
    "olist_order_reviews_dataset.csv": ("order_reviews", [
        "review_creation_date", "review_answer_timestamp",
    ]),
    "olist_products_dataset.csv": ("products", []),
    "olist_sellers_dataset.csv": ("sellers", []),
    "product_category_name_translation.csv": ("category_translation", []),
}

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def statement(cursor, query: str):
    cursor.execute(query)
    return cursor.fetchall() if cursor.description else []


def main() -> None:
    host = required_env("DATABRICKS_SERVER_HOSTNAME").removeprefix("https://").rstrip("/")
    http_path = required_env("DATABRICKS_HTTP_PATH")
    token = required_env("DATABRICKS_TOKEN")
    catalog = os.getenv("DATABRICKS_CATALOG", "main")
    schema = os.getenv("DATABRICKS_SCHEMA", "kpi")
    volume = os.getenv("DATABRICKS_VOLUME", "raw")
    volume_root = os.getenv(
        "DATABRICKS_VOLUME_ROOT", f"/Volumes/{catalog}/{schema}/{volume}"
    ).rstrip("/")
    for label, value in [("catalog", catalog), ("schema", schema), ("volume", volume)]:
        if not value.replace("_", "").isalnum():
            raise SystemExit(f"Unsafe {label} identifier: {value!r}")

    missing = [name for name in FILES if not (RAW / name).is_file()]
    if missing:
        raise SystemExit(
            "Missing raw CSV files in data/raw/: " + ", ".join(missing)
            + ". Download the nine Olist files listed in docs/data_dictionary.md."
        )

    # Databricks SDK Files API supports volume file upload. Its workspace
    # client is authenticated using the same host/token as the SQL connector.
    from databricks.sdk import WorkspaceClient
    workspace = WorkspaceClient(host=f"https://{host}", token=token)
    started = datetime.now(timezone.utc)
    results: dict[str, int] = {}

    with sql.connect(server_hostname=host, http_path=http_path, access_token=token) as conn:
        with conn.cursor() as cur:
            statement(cur, f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
            statement(cur, f"USE CATALOG `{catalog}`")
            statement(cur, f"USE SCHEMA `{schema}`")
            statement(cur, f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`{volume}`")
            for filename, (table, timestamp_cols) in FILES.items():
                local = RAW / filename
                remote = f"{volume_root}/{filename}"
                workspace.files.upload_from(remote, str(local), overwrite=True)
                # read_files handles multiline review text; the CSV schema
                # is inferred by Spark and known timestamp fields are parsed.
                timestamp_expr = ", ".join(
                    f"to_timestamp(`{col}`) AS `{col}`" for col in timestamp_cols
                )
                quoted_timestamp_cols = ", ".join("`" + col + "`" for col in timestamp_cols)
                projection = f"* EXCEPT ({quoted_timestamp_cols})" if quoted_timestamp_cols else "*"
                if timestamp_expr:
                    projection += ", " + timestamp_expr
                create = (
                    f"CREATE OR REPLACE TABLE `{catalog}`.`{schema}`.`{table}` AS "
                    f"SELECT {projection} FROM read_files('{remote}', "
                    "format => 'csv', header => true, inferColumnTypes => true, "
                    "multiLine => true, quote => '\"', escape => '\"')"
                )
                statement(cur, create)
                rows = statement(
                    cur, f"SELECT COUNT(*) FROM `{catalog}`.`{schema}`.`{table}`"
                )[0][0]
                results[table] = int(rows)
                print(f"Loaded {table}: {rows:,} rows")

            for filename in ["01_clean_orders.sql", "02_master_table.sql", "03_kpi_monthly.sql"]:
                statement(cur, (SQL_DIR / filename).read_text(encoding="utf-8"))
                print(f"Executed {filename}")

            recon_sql = (SQL_DIR / "04_reconcile.sql").read_text(encoding="utf-8")
            cur.execute(recon_sql)
            columns = [d[0] for d in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            if len(rows) != 11 or any(row["result"] != "MATCH" for row in rows):
                raise RuntimeError(
                    "Databricks reconciliation failed: "
                    + json.dumps(rows, default=str)
                )

    finished = datetime.now(timezone.utc)
    receipt = {
        "status": "PASS",
        "executed_on_databricks": True,
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 2),
        "workspace_host": f"https://{host}",
        "http_path": http_path,
        "catalog_schema": f"{catalog}.{schema}",
        "volume": volume_root,
        "source_row_counts": results,
        "reconciliation": {
            "matched": len(rows),
            "total": len(rows),
            "metrics": rows,
        },
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, default=str))
    print(f"Receipt written: {RECEIPT.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (DatabricksError, OSError, RuntimeError) as exc:
        print(f"Databricks run failed: {exc}", file=sys.stderr)
        raise
