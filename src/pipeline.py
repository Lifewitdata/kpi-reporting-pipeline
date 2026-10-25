"""One-command refresh for the KPI reporting pipeline.

Usage, from the repository root:
    pip install -r requirements.txt
    python src/pipeline.py

Steps:
  1. Load the 9 raw CSVs from data/raw/ into data/olist.db (SQLite).
  2. Run sql/01_clean_orders.sql, 02_master_table.sql,
     03_kpi_monthly.sql in order.
  3. Run the data quality checks (warnings are logged, not hidden).
  4. Export refresh-ready tables to data/processed/:
       master_orders.csv       - one row per order (the reporting table)
       kpi_monthly.csv         - one row per purchase month, 8 KPIs
       category_monthly.csv    - item-grain category revenue by month
                                 (for the dashboard Top 10 categories;
                                 item price, NOT payment_value, so it
                                 is never double-counted)
       delivery_by_state.csv   - delivered orders, on-time rate and
                                 average delivery days by customer state
  5. Write logs/pipeline_run.log with run time and row counts.

On Alteryx this same flow would be a drag-and-drop workflow:
Input Data -> Select/Clean -> Join -> Summarize -> Output Data,
with the quality checks as a Test tool. The logic is identical;
only the tool changes.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from config import (  # noqa: E402
    DATA_PROCESSED,
    DB_PATH,
    LOG_DIR,
    SQL_FILES_IN_ORDER,
)
from load_data import load_data  # noqa: E402
from quality_checks import run_quality_checks  # noqa: E402
from run_sql import run_sql_files  # noqa: E402

CATEGORY_SQL = """
SELECT
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
    COALESCE(t.product_category_name_english, p.product_category_name,
             'unknown') AS category,
    SUM(i.price) AS item_revenue,
    COUNT(DISTINCT i.order_id) AS orders,
    COUNT(*) AS items
FROM order_items AS i
JOIN clean_orders AS o ON i.order_id = o.order_id
LEFT JOIN products AS p ON i.product_id = p.product_id
LEFT JOIN category_translation AS t
    ON p.product_category_name = t.product_category_name
WHERE o.is_delivered = 1
GROUP BY order_month, category
ORDER BY order_month, item_revenue DESC
"""

STATE_SQL = """
SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    AVG(on_time_flag) AS on_time_rate,
    AVG(delivery_days) AS avg_delivery_days,
    AVG(review_score) AS avg_review_score
FROM master_orders
WHERE is_delivered = 1
GROUP BY customer_state
ORDER BY delivered_orders DESC
"""


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "pipeline_run.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger(__name__)
    started = datetime.now()
    logger.info("Pipeline run started at %s", started.isoformat())

    loaded = load_data()
    for table, rows in loaded.items():
        logger.info("Loaded table %s: %s rows", table, rows)

    run_sql_files(SQL_FILES_IN_ORDER)

    checks = run_quality_checks()

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        master_rows = conn.execute(
            text("SELECT COUNT(*) FROM master_orders")
        ).scalar()
    if master_rows == 0:
        raise RuntimeError("master_orders is empty; refusing to export.")
    logger.info("master_orders: %s rows", master_rows)

    exports = {}
    with engine.connect() as conn:
        for name, query in [
            ("master_orders", "SELECT * FROM master_orders ORDER BY order_purchase_timestamp"),
            ("kpi_monthly", "SELECT * FROM kpi_monthly ORDER BY order_month"),
            ("category_monthly", CATEGORY_SQL),
            ("delivery_by_state", STATE_SQL),
        ]:
            df = pd.read_sql(query, conn)
            out = DATA_PROCESSED / f"{name}.csv"
            df.to_csv(out, index=False)
            exports[name] = len(df)
            logger.info("Exported %s: %s rows -> %s", name, len(df), out)

    logger.info("Quality checks: %s", checks)
    logger.info(
        "Pipeline run finished in %.1f seconds. Exports: %s",
        (datetime.now() - started).total_seconds(),
        exports,
    )
    print(f"Done. Exports: {exports}. Log: {log_path}")


if __name__ == "__main__":
    main()
