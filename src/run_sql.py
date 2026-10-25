"""Execute the numbered .sql files in order against SQLite.

Each numbered file contains a DROP TABLE IF EXISTS followed by a
CREATE TABLE AS, so it is executed with sqlite3's executescript()
rather than a single-statement SQLAlchemy call (which rejects a file
with two statements). The data-quality file (04) is SELECT-only and
is run by quality_checks.py, not here, so a check can never change data.
"""

import logging
import sqlite3
from pathlib import Path

from config import DB_PATH, SQL_DIR

logger = logging.getLogger(__name__)


def run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(sql)
    logger.info("Ran %s", path.name)


def run_sql_files(filenames) -> None:
    for name in filenames:
        run_sql_file(SQL_DIR / name)
