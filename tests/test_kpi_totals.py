import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data/processed/master_orders.csv"
MONTHLY = ROOT / "data/processed/kpi_monthly.csv"


def test_master_orders_totals():
    df = pd.read_csv(MASTER)
    assert len(df) == 99441
    delivered = df[df["is_delivered"] == 1]
    assert len(delivered) == 96478
    assert abs(delivered["payment_value_total"].sum() - 15422461.77) < 0.01


def test_on_time_rate():
    df = pd.read_csv(MASTER)
    delivered = df[df["is_delivered"] == 1]
    rate = delivered["on_time_flag"].dropna().mean()
    assert abs(rate - 0.9189) < 0.001


def test_kpi_monthly_matches_master():
    monthly = pd.read_csv(MONTHLY)
    assert monthly["total_orders"].sum() == 99441
    assert abs(monthly["total_revenue"].sum() - 15422461.77) < 0.01
