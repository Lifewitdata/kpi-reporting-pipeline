"""Load the 9 raw Olist CSVs into SQLite.

One table per CSV, no cleaning here: cleaning lives in SQL so the
transformation is visible and reviewable. Run standalone with
``python src/load_data.py`` or as step 1 of ``src/pipeline.py``.
"""

import logging

import pandas as pd
from sqlalchemy import create_engine

from config import DATA_RAW, DB_PATH, TABLES

logger = logging.getLogger(__name__)


def load_data() -> dict:
    """Load every CSV in TABLES into SQLite. Returns {table: rows}."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    counts = {}
    for csv_name, table in TABLES.items():
        path = DATA_RAW / csv_name
        if not path.exists():
            raise FileNotFoundError(
                f"Missing raw file: {path}. Download the Brazilian "
                "E-Commerce dataset from Kaggle into data/raw/ first "
                "(see README, 'How to run')."
            )
        df = pd.read_csv(path)
        df.to_sql(table, engine, if_exists="replace", index=False)
        counts[table] = len(df)
        logger.info("Loaded %s: %s rows -> table '%s'", csv_name, len(df), table)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print(load_data())
