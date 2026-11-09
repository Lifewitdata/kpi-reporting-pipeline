"""Run the ad-hoc request queries in sql/ad-hoc/ against the processed tables.

Usage, from the repository root:
    python src/run_adhoc.py            # run all
    python src/run_adhoc.py 03         # run files whose name starts with 03

Loads data/processed/master_orders.csv and category_monthly.csv into an
in-memory SQLite database, so no raw Kaggle download is needed.
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from config import DATA_PROCESSED, SQL_DIR  # noqa: E402

ADHOC_DIR = SQL_DIR / "ad-hoc"
TABLES = ["master_orders", "category_monthly"]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for table in TABLES:
        pd.read_csv(DATA_PROCESSED / f"{table}.csv").to_sql(table, conn, index=False)
    return conn


def main(prefix: str = "") -> None:
    conn = connect()
    for path in sorted(ADHOC_DIR.glob(f"{prefix}*.sql")):
        result = pd.read_sql(path.read_text(encoding="utf-8"), conn)
        print(f"\n## {path.name}\n")
        print(result.to_markdown(index=False, floatfmt=",.2f"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
