# Databricks execution

The repository includes a runner that submits the Spark SQL port to a
real Databricks SQL warehouse. The DuckDB-based checker remains a local
equivalence test and is not a substitute for live execution.

## Prerequisites and permissions

The Databricks identity used for the run needs:
- permission to use the SQL warehouse;
- permission to create/use the target catalog schema and managed volume;
- permission to create or replace tables in the schema;
- permission to upload files to and read files from the Unity Catalog volume.

Unity Catalog must be enabled. The default target is `main.kpi.raw`.

## Run locally

Download the nine source files listed in `docs/data_dictionary.md` from
the [Olist Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
into `data/raw/`. Then install:

```bash
pip install -r requirements.txt
```

Set these environment variables. Never commit the token:

| Variable | Required | Default / example |
|---|---:|---|
| `DATABRICKS_SERVER_HOSTNAME` | Yes | `adb-<workspace-id>.<number>.azuredatabricks.net` |
| `DATABRICKS_HTTP_PATH` | Yes | `/sql/1.0/warehouses/<warehouse-id>` |
| `DATABRICKS_TOKEN` | Yes | Workspace token |
| `DATABRICKS_CATALOG` | No | `main` |
| `DATABRICKS_SCHEMA` | No | `kpi` |
| `DATABRICKS_VOLUME` | No | `raw` |
| `DATABRICKS_VOLUME_ROOT` | No | `/Volumes/main/kpi/raw` |

PowerShell:

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

The runner uploads the nine CSVs to the Unity Catalog volume, creates or
replaces their source tables, runs `01_clean_orders.sql`,
`02_master_table.sql`, and `03_kpi_monthly.sql`, then executes
`04_reconcile.sql`. It exits non-zero unless all 11 rows report MATCH.
The JSON receipt is written only after the complete run passes.

## GitHub Actions (manual live run)

The workflow `.github/workflows/databricks.yml` is triggered with
**Actions → Databricks SQL validation → Run workflow**. Configure these
repository secrets first:

- `KAGGLE_API_TOKEN`: Kaggle API token used to download the public Olist dataset;
- `DATABRICKS_SERVER_HOSTNAME`;
- `DATABRICKS_HTTP_PATH`;
- `DATABRICKS_TOKEN`.

Optional repository variables: `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`,
and `DATABRICKS_VOLUME`. Defaults are `main`, `kpi`, and `raw`.
The workflow downloads source data, executes against the warehouse, uploads
the receipt as a workflow artifact, and commits a successful receipt to the
branch selected when the workflow is started. Repository rules may require
that the receipt commit be made through a pull request instead.

## Evidence and validation boundaries

- `python src/check_databricks_port.py`: local DuckDB/Spark-SQL equivalence only.
- `python scripts/run_databricks.py`: actual Databricks SQL warehouse run.
- The receipt records status, UTC timestamps, workspace host, SQL HTTP path,
  catalog/schema, volume, raw input row counts, and all 11 reconciliation
  results. It does not contain the access token.
- Do not claim Databricks execution until the receipt says `PASS` and all
  11 metrics say `MATCH`.

## Expected reconciliation

The query expects 11/11 MATCH, including 99,441 clean/master rows,
96,478 delivered orders, R$15,422,461.77 delivered revenue,
R$13,221,498.11 delivered item price, 25 monthly rows,
91.89% on-time delivery, 12.56 average delivery days, 4.16 average
review score, and 8 delivered orders without a delivery date.
