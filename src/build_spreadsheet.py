"""Build spreadsheets/Olist_KPI_Spreadsheet.xlsx from the processed tables.

Usage, from the repository root (Windows + desktop Excel required):
    python src/build_spreadsheet.py

Two stages: openpyxl writes the data sheets, formulas and validation,
then Excel itself adds the native PivotTables, recalculates and saves.
Excel is required because openpyxl cannot create a PivotTable.

Order category is derived here from the raw item table (the category of
the order's highest-priced item), because category is item grain and is
deliberately absent from master_orders. This is what lets the category
pivot total to the order-level revenue.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402
from openpyxl.worksheet.table import Table, TableStyleInfo  # noqa: E402

from config import DATA_PROCESSED, DATA_RAW, ROOT  # noqa: E402

OUT_DIR = ROOT / "spreadsheets"
OUT_PATH = OUT_DIR / "Olist_KPI_Spreadsheet.xlsx"

EXPECTED_REVENUE = 15422461.77
EXPECTED_ORDERS = 99441
EXPECTED_ITEM_REVENUE = 13221498.11

ORDER_COLUMNS = [
    "order_id", "order_month", "customer_state", "order_status",
    "order_category", "is_delivered", "revenue_delivered",
    "delivery_days", "on_time_flag", "review_score",
    "dated_delivered", "on_time_orders", "item_count",
]
CATEGORY_COLUMNS = ["order_month", "category", "item_revenue", "orders", "items"]

BOLD = Font(bold=True)
MONEY = '#,##0.00'
PERCENT = '0.00%'


def order_categories() -> pd.Series:
    """Category of each order's highest-priced item (ties: lowest item id)."""
    items = pd.read_csv(DATA_RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(DATA_RAW / "olist_products_dataset.csv")
    translation = pd.read_csv(DATA_RAW / "product_category_name_translation.csv")
    items = items.merge(
        products[["product_id", "product_category_name"]], on="product_id", how="left"
    ).merge(translation, on="product_category_name", how="left")
    items["category"] = (
        items["product_category_name_english"]
        .fillna(items["product_category_name"])
        .fillna("unknown")
    )
    top = (
        items.sort_values(["order_id", "price", "order_item_id"],
                          ascending=[True, False, True])
        .drop_duplicates("order_id")
        .set_index("order_id")["category"]
    )
    return top


def load_orders() -> pd.DataFrame:
    orders = pd.read_csv(DATA_PROCESSED / "master_orders.csv")
    orders["order_category"] = (
        orders["order_id"].map(order_categories()).fillna("no_items")
    )
    orders["dated_delivered"] = (
        (orders["is_delivered"] == 1) & orders["on_time_flag"].notna()
    ).astype(int)
    orders["on_time_orders"] = orders["on_time_flag"].fillna(0).astype(int)
    return orders[ORDER_COLUMNS]


def write_table(ws, df: pd.DataFrame, name: str) -> None:
    ws.append(list(df.columns))
    for cell in ws[1]:
        cell.font = BOLD
    for row in df.itertuples(index=False, name=None):
        ws.append([None if pd.isna(v) else v for v in row])
    ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
    table = Table(displayName=name, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9", showRowStripes=True
    )
    ws.add_table(table)
    ws.freeze_panes = "A2"
    for idx, column in enumerate(df.columns, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = max(14, len(column) + 2)


PIVOT_SHEETS = ["Pivot by Month", "Pivot by Category", "Pivot Item Revenue"]


def build_base(orders: pd.DataFrame, category: pd.DataFrame,
               monthly: pd.DataFrame) -> None:
    wb = Workbook()

    readme = wb.active
    readme.title = "Read me"
    readme.column_dimensions["A"].width = 110
    lines = [
        ("Olist KPI spreadsheet", True),
        ("Built from data/processed/ by src/build_spreadsheet.py. "
         "Money in Brazilian reais (R$).", False),
        ("", False),
        ("Orders - one row per order (99,441). The reporting table, plus "
         "order_category: the category of the order's highest-priced item.", False),
        ("Category - month x category item revenue (item price, no freight). "
         "Never sum order payments here.", False),
        ("Monthly KPIs - the 8 KPIs per purchase month. Filter is_full_month = 1 "
         "for trends.", False),
        ("Pivot by Month / Pivot by Category - native PivotTables on Orders. "
         "Both total to R$ 15,422,461.77.", False),
        ("Pivot Item Revenue - native PivotTable on Category; totals "
         "R$ 13,221,498.11 (item price, so it is not the payment total).", False),
        ("Order Lookup - paste an order_id; XLOOKUP and INDEX/MATCH return "
         "its details.", False),
        ("Selector - pick a month and a category from the dropdowns.", False),
        ("Checks - live formulas comparing this workbook with the SQL totals.", False),
        ("", False),
        ("Category attribution: an order with items from several categories is "
         "counted once, under its highest-priced item's category. That is why "
         "Pivot by Category can total the order revenue without double-counting. "
         "For true item-level category revenue use Pivot Item Revenue.", False),
        ("Refresh: re-run the pipeline, then python src/build_spreadsheet.py. "
         "Requires desktop Excel on Windows.", False),
    ]
    for text, bold in lines:
        readme.append([text])
        cell = readme.cell(row=readme.max_row, column=1)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if bold:
            cell.font = Font(bold=True, size=14)

    ws_orders = wb.create_sheet("Orders")
    write_table(ws_orders, orders, "tblOrders")
    for row in ws_orders.iter_rows(min_row=2, min_col=7, max_col=8):
        for cell in row:
            cell.number_format = MONEY

    ws_category = wb.create_sheet("Category")
    write_table(ws_category, category[CATEGORY_COLUMNS], "tblCategory")
    for row in ws_category.iter_rows(min_row=2, min_col=3, max_col=3):
        row[0].number_format = MONEY

    ws_monthly = wb.create_sheet("Monthly KPIs")
    write_table(ws_monthly, monthly, "tblMonthly")
    for row in ws_monthly.iter_rows(min_row=2):
        for idx in (6, 9, 12):
            row[idx - 1].number_format = PERCENT
        for idx in (7, 8, 10):
            row[idx - 1].number_format = MONEY

    # Created empty so the Checks formulas reference sheets that exist;
    # otherwise Excel rewrites them as links to an external workbook.
    for name in PIVOT_SHEETS:
        wb.create_sheet(name)

    lists = wb.create_sheet("Lists")
    lists.append(["month", "category", "item_category"])
    months = sorted(monthly["order_month"].unique())
    order_cats = sorted(orders["order_category"].unique())
    item_cats = sorted(category["category"].unique())
    for idx in range(max(len(months), len(order_cats), len(item_cats))):
        lists.append([
            months[idx] if idx < len(months) else None,
            order_cats[idx] if idx < len(order_cats) else None,
            item_cats[idx] if idx < len(item_cats) else None,
        ])
    for name, column, count in [
        ("MonthList", "A", len(months)),
        ("CategoryList", "B", len(order_cats)),
        ("ItemCategoryList", "C", len(item_cats)),
    ]:
        wb.defined_names.add(_defined_name(name, f"Lists!${column}$2:${column}${count + 1}"))
    wb.defined_names.add(_defined_name("OrderIdList", f"Orders!$A$2:$A${len(orders) + 1}"))
    lists.sheet_state = "hidden"

    lookup = wb.create_sheet("Order Lookup")
    lookup.column_dimensions["A"].width = 26
    lookup.column_dimensions["B"].width = 40
    lookup["A1"] = "Order lookup"
    lookup["A1"].font = Font(bold=True, size=14)
    lookup["A3"] = "Order ID (pick or paste)"
    lookup["B3"] = orders.loc[orders["revenue_delivered"].idxmax(), "order_id"]
    fields = [
        ("Category (XLOOKUP)", "order_category"),
        ("Delivery days (INDEX/MATCH)", "delivery_days"),
        ("Revenue (XLOOKUP)", "revenue_delivered"),
        ("Month (XLOOKUP)", "order_month"),
        ("State (XLOOKUP)", "customer_state"),
        ("Status (XLOOKUP)", "order_status"),
        ("Review score (INDEX/MATCH)", "review_score"),
    ]
    for offset, (label, column) in enumerate(fields, start=5):
        lookup.cell(row=offset, column=1, value=label)
        letter = get_column_letter(ORDER_COLUMNS.index(column) + 1)
        target = f"Orders!${letter}$2:${letter}${len(orders) + 1}"
        if "INDEX/MATCH" in label:
            formula = (f'=IFERROR(INDEX({target},MATCH($B$3,OrderIdList,0)),'
                       '"not found / not applicable")')
        else:
            # openpyxl writes formulas verbatim; Excel needs the _xlfn
            # prefix for XLOOKUP or it loads as an unknown function.
            formula = (f'=IFERROR(_xlfn.XLOOKUP($B$3,OrderIdList,{target}),'
                       '"order not found")')
        cell = lookup.cell(row=offset, column=2, value=formula)
        if column in ("revenue_delivered", "delivery_days"):
            cell.number_format = MONEY
    dv = DataValidation(type="list", formula1="=OrderIdList", allow_blank=True)
    dv.error = "Pick an order_id from the Orders sheet."
    lookup.add_data_validation(dv)
    dv.add(lookup["B3"])

    selector = wb.create_sheet("Selector")
    selector.column_dimensions["A"].width = 38
    selector.column_dimensions["B"].width = 22
    selector["A1"] = "Pick a month and a category"
    selector["A1"].font = Font(bold=True, size=14)
    selector["A3"], selector["B3"] = "Month", "2017-11"
    selector["A4"], selector["B4"] = "Order category", "health_beauty"
    selector["A5"], selector["B5"] = "Item category", "health_beauty"
    for cell, source in [("B3", "=MonthList"), ("B4", "=CategoryList"),
                         ("B5", "=ItemCategoryList")]:
        dv = DataValidation(type="list", formula1=source, allow_blank=False)
        dv.error = "Pick a value from the dropdown."
        dv.showErrorMessage = True
        selector.add_data_validation(dv)
        dv.add(selector[cell])
    rows = [
        ("Revenue, that month (all categories)",
         '=SUMIFS(tblOrders[revenue_delivered],tblOrders[order_month],$B$3)', MONEY),
        ("Orders, that month",
         '=COUNTIFS(tblOrders[order_month],$B$3)', '#,##0'),
        ("On-time rate, that month",
         '=IFERROR(SUMIFS(tblOrders[on_time_orders],tblOrders[order_month],$B$3)'
         '/SUMIFS(tblOrders[dated_delivered],tblOrders[order_month],$B$3),"n/a")', PERCENT),
        ("Revenue, month + order category",
         '=SUMIFS(tblOrders[revenue_delivered],tblOrders[order_month],$B$3,'
         'tblOrders[order_category],$B$4)', MONEY),
        ("Orders, month + order category",
         '=COUNTIFS(tblOrders[order_month],$B$3,tblOrders[order_category],$B$4)', '#,##0'),
        ("Item revenue, month + item category",
         '=SUMIFS(tblCategory[item_revenue],tblCategory[order_month],$B$3,'
         'tblCategory[category],$B$5)', MONEY),
        ("Revenue, that order category (all months)",
         '=SUMIFS(tblOrders[revenue_delivered],tblOrders[order_category],$B$4)', MONEY),
    ]
    for offset, (label, formula, fmt) in enumerate(rows, start=7):
        selector.cell(row=offset, column=1, value=label)
        cell = selector.cell(row=offset, column=2, value=formula)
        cell.number_format = fmt

    checks = wb.create_sheet("Checks")
    checks.column_dimensions["A"].width = 46
    for column in ("B", "C", "D"):
        checks.column_dimensions[column].width = 20
    checks.append(["Check", "This workbook", "SQL total", "Result"])
    for cell in checks[1]:
        cell.font = BOLD
    last_month = len(months) + 1
    check_rows = [
        ("Order revenue = SQL revenue",
         "=ROUND(SUM(tblOrders[revenue_delivered]),2)", EXPECTED_REVENUE),
        ("Order rows = SQL order count", "=COUNTA(tblOrders[order_id])", EXPECTED_ORDERS),
        ("Monthly KPI revenue = SQL revenue",
         f"=ROUND(SUM('Monthly KPIs'!$G$2:$G${last_month}),2)", EXPECTED_REVENUE),
        ("Category item revenue = SQL item revenue",
         "=ROUND(SUM(tblCategory[item_revenue]),2)", EXPECTED_ITEM_REVENUE),
        ("Pivot by Month total = SQL revenue",
         "=ROUND(GETPIVOTDATA(\"Revenue (R$)\",'Pivot by Month'!$A$4),2)",
         EXPECTED_REVENUE),
        ("Pivot by Category total = SQL revenue",
         "=ROUND(GETPIVOTDATA(\"Revenue (R$)\",'Pivot by Category'!$A$4),2)",
         EXPECTED_REVENUE),
        ("Pivot Item Revenue total = SQL item revenue",
         "=ROUND(GETPIVOTDATA(\"Item revenue (R$)\",'Pivot Item Revenue'!$A$4),2)",
         EXPECTED_ITEM_REVENUE),
    ]
    for row_index, (label, formula, expected) in enumerate(check_rows, start=2):
        checks.cell(row=row_index, column=1, value=label)
        checks.cell(row=row_index, column=2, value=formula).number_format = MONEY
        checks.cell(row=row_index, column=3, value=expected).number_format = MONEY
        checks.cell(
            row=row_index, column=4,
            value=f'=IF(ROUND(B{row_index},2)=ROUND(C{row_index},2),"MATCH","MISMATCH")',
        )
    wb.save(OUT_PATH)


def _defined_name(name: str, refers_to: str):
    from openpyxl.workbook.defined_name import DefinedName

    return DefinedName(name, attr_text=refers_to)


def add_pivots() -> dict:
    """Excel adds the native PivotTables, recalculates and saves."""
    import win32com.client as win32

    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    results = {}
    try:
        wb = excel.Workbooks.Open(str(OUT_PATH))
        specs = [
            ("Pivot by Month", "tblOrders", "order_month",
             [("revenue_delivered", "Revenue (R$)"), ("order_id", "Order count")]),
            ("Pivot by Category", "tblOrders", "order_category",
             [("revenue_delivered", "Revenue (R$)"), ("order_id", "Order count")]),
            ("Pivot Item Revenue", "tblCategory", "category",
             [("item_revenue", "Item revenue (R$)"), ("items", "Item count")]),
        ]
        for sheet_name, source, row_field, measures in specs:
            ws = wb.Worksheets(sheet_name)
            cache = wb.PivotCaches().Create(SourceType=1, SourceData=source)
            pivot = cache.CreatePivotTable(
                TableDestination=f"'{sheet_name}'!R3C1", TableName=sheet_name.replace(" ", "")
            )
            pivot.PivotFields(row_field).Orientation = 1  # xlRowField
            for field, caption in measures:
                pf = pivot.PivotFields(field)
                pf.Orientation = 4  # xlDataField
                pf.Function = -4157 if field != "order_id" else -4112  # xlSum / xlCount
                pf.Caption = caption
                pf.NumberFormat = MONEY if "revenue" in field else "#,##0"
            if source == "tblOrders":
                calc = pivot.CalculatedFields().Add(
                    "OnTimeRate", "=on_time_orders / dated_delivered", True
                )
                calc.Orientation = 4
                calc.Caption = "On-time rate"
                calc.NumberFormat = PERCENT
                pivot.PivotFields(row_field).AutoSort(2, "Revenue (R$)")  # xlDescending
            pivot.RowGrand = True
            pivot.ColumnGrand = True
            # Sep/Oct 2018 have no delivered orders, so the on-time rate
            # divides by zero there. Show n/a, not 0%.
            pivot.DisplayErrorString = True
            pivot.ErrorString = "n/a"
            ws.Columns("A:D").AutoFit()
            pivot.RefreshTable()
        wb.Application.CalculateFullRebuild()
        checks = wb.Worksheets("Checks")
        for row in range(2, 9):
            results[checks.Cells(row, 1).Value] = (
                checks.Cells(row, 2).Value, checks.Cells(row, 4).Value
            )
        wb.Save()
        wb.Close(SaveChanges=False)
    finally:
        excel.Quit()
    return results


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    orders = load_orders()
    category = pd.read_csv(DATA_PROCESSED / "category_monthly.csv")
    monthly = pd.read_csv(DATA_PROCESSED / "kpi_monthly.csv")
    build_base(orders, category, monthly)
    print(f"Base workbook written: {OUT_PATH}")
    for label, (value, status) in add_pivots().items():
        print(f"{status:9} {label}: {value}")


if __name__ == "__main__":
    main()
