# Databricks execution

This run path executes against a real Databricks SQL warehouse; unlike
`src/check_databricks_port.py`, it does not emulate Spark SQL locally.

## Prerequisites

- A Databricks workspace with a running SQL warehouse.
- A personal access token (or supported token) able to use the warehouse,
  create schemas/tables/volumes, and upload files to Unity Catalog.
- Unity Catalog enabled and permission to create/use the configured catalog,
  schema, and volume.
- The nine Olist CSVs in `data/raw/` (see `docs/data_dictionary.md`).

## Configure

Install dependencies:

```bash
pip install -r requirements.txt
```

Set these environment variables. Do not commit credentials:

| Variable | Required | Example |
|---|---:|---|
| `DATABRICKS_SERVER_HOSTNAME` | Yes | `adb-<workspace-id>.<number>.azuredatabricks.net` (hostname only or URL) |
| `DATABRICKS_HTTP_PATH` | Yes | SQL warehouse HTTP path from warehouse connection details |
| `DATABRICKS_TOKEN` | Yes | Workspace access token |
| `DATABRICKS_CATALOG` | No | `main` |
| `DATABRICKS_SCHEMA` | No | `kpi` |
| `DATABRICKS_VOLUME` | No | `raw` |
| `DATABRICKS_VOLUME_ROOT` | No | Defaults to `/Volumes/<catalog>/<schema>/<volume>` |

PowerShell example:

```powershell
$env:DATABRICKS_SERVER_HOSTNAME = "adb-xxxxxxxxxxxxxxxx.x.azuredatabricks.net"
$env:DATABRICKS_HTTP_PATH = "/sql/1.0/warehouses/xxxxxxxxxxxxxxxx"
$env:DATABRICKS_TOKEN = "<your-token>"
python scripts/run_databricks.py
```

macOS/Linux:

```bash
export DATABRICKS_SERVER_HOSTNAME="adb-xxxxxxxxxxxxxxxx.x.azuredatabricks.net"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/xxxxxxxxxxxxxxxx"
export DATABRICKS_TOKEN="<your-token>"
python scripts/run_databricks.py
```

The runner creates the schema and volume if permitted, uploads all nine CSVs,
creates/replaces the raw tables, runs SQL 01–03, and checks the 11 expected
reconciliation metrics using SQL 04. It writes
`docs/databricks-run-receipt.json` only after all 11 rows report `MATCH`.
A failed run exits non-zero and does not overwrite the prior successful receipt.

## Validation boundaries

- `python src/check_databricks_port.py` is a **local DuckDB equivalence test**.
- `python scripts/run_databricks.py` is the **real warehouse execution**.
- Never claim a Databricks run based on the local test alone.
- The receipt records UTC timestamps, workspace hostname, warehouse HTTP path,
  catalog/schema, volume, raw-table row counts and reconciliation details.
  Review it before claiming successful execution.

## Expected results

The reconciliation expects 11/11 MATCH, including 99,441 clean/master rows,
96,478 delivered orders, R$15,422,461.77 delivered revenue, 25 monthly rows,
91.89% on-time delivery, 12.56 average delivery days, 4.16 average review
score and 8 delivered orders without a delivery date.
