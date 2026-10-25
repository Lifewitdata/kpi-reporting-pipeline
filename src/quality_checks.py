"""Data quality checks for the KPI pipeline.

Runs the SELECT-only checks in sql/04_data_quality_checks.sql and a
few Python-side reconciliations (raw CSV row counts vs loaded tables).
A WARNING is logged, not raised: the spec for this project is that a
failed check logs a warning so a bad refresh is visible. The pipeline
only stops if master_orders is empty, because then there is nothing
to report.
"""

import logging

import pandas as pd
from sqlalchemy import create_engine, text

from config import DATA_RAW, DB_PATH, SQL_DIR, TABLES

logger = logging.getLogger(__name__)


def run_quality_checks() -> list:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    sql = (SQL_DIR / "04_data_quality_checks.sql").read_text(encoding="utf-8")
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    results = []
    for check_name, actual_value, status in rows:
        results.append(
            {"check": check_name, "actual": actual_value, "status": status}
        )
        if status == "WARNING":
            logger.warning("DQ WARNING: %s = %s", check_name, actual_value)
        else:
            logger.info("DQ %s: %s = %s", status, check_name, actual_value)

    # Raw CSV row counts vs loaded tables (pandas handles the quoted
    # multi-line review comments; `wc -l` does not, see DQ log).
    with engine.connect() as conn:
        for csv_name, table in TABLES.items():
            expected = len(pd.read_csv(DATA_RAW / csv_name))
            actual = conn.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar()
            ok = expected == actual
            results.append(
                {"check": f"load_{table}", "actual": actual, "status": "PASS" if ok else "WARNING"}
            )
            if not ok:
                logger.warning(
                    "DQ WARNING: load_%s expected %s rows, got %s",
                    table, expected, actual,
                )
    return results
