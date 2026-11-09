# Databricks notebook source
# 00_load_raw.py — run this as a Databricks notebook cell (Python).
#
# Upload the 9 Olist CSVs to a Unity Catalog volume first, e.g.
#   /Volumes/main/kpi/raw/
# then set CATALOG/SCHEMA/VOLUME below and run all cells.
#
# Timestamps are cast explicitly: CSV inference would leave them as
# strings, and the date arithmetic in 01_clean_orders.sql needs real
# timestamps to match the SQLite pipeline.

CATALOG = "main"
SCHEMA = "kpi"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/raw"

from pyspark.sql import functions as F  # noqa: E402

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE {CATALOG}.{SCHEMA}")

TABLES = {
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

for filename, (table, timestamps) in TABLES.items():
    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("multiLine", True)      # review comments contain newlines
        .option("escape", '"')
        .csv(f"{VOLUME_PATH}/{filename}")
    )
    for column in timestamps:
        df = df.withColumn(column, F.to_timestamp(column))
    df.write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.{table}")
    print(table, df.count())
