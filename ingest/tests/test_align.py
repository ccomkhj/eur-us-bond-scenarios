import pandas as pd
from eur_us_bond_ingest.align import build_daily_panel, build_monthly_panel


def _series(dates, values, name):
    s = pd.Series(values, index=pd.to_datetime(dates), name=name)
    s.index.name = "date"
    return s


def test_build_daily_panel_reindexes_to_business_days_ffills_and_adds_spreads():
    series = {
        "eurusd": _series(["2020-01-02", "2020-01-06"], [1.12, 1.13], "eurusd"),
        "ust10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.90, 1.85, 1.80], "ust10y"),
        "bund10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [-0.20, -0.25, -0.30], "bund10y"),
        "ust2y": _series(["2020-01-02", "2020-01-06"], [1.55, 1.50], "ust2y"),
        "schatz2y": _series(["2020-01-02", "2020-01-06"], [-0.60, -0.62], "schatz2y"),
        "fed_funds": _series(["2020-01-02", "2020-01-06"], [1.55, 1.55], "fed_funds"),
        "ecb_rate": _series(["2020-01-02", "2020-01-06"], [-0.50, -0.50], "ecb_rate"),
        "dxy": _series(["2020-01-02", "2020-01-06"], [96.0, 96.5], "dxy"),
        "brent": _series(["2020-01-02", "2020-01-06"], [66.0, 68.0], "brent"),
    }
    df = build_daily_panel(series)
    assert list(df.index) == [pd.Timestamp(d) for d in ["2020-01-02", "2020-01-03", "2020-01-06"]]
    assert df.loc["2020-01-03", "eurusd"] == 1.12
    assert df.loc["2020-01-02", "spread10y"] == 1.90 - (-0.20)
    assert df.loc["2020-01-06", "spread2y"] == 1.50 - (-0.62)
    assert df.index.name == "date"


def test_build_daily_panel_does_not_backfill_leading_gaps():
    series = {
        "eurusd": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.12, 1.12, 1.13], "eurusd"),
        "ust10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.90, 1.85, 1.80], "ust10y"),
        "bund10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [-0.20, -0.25, -0.30], "bund10y"),
        "ust2y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.55, 1.52, 1.50], "ust2y"),
        "schatz2y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [-0.60, -0.61, -0.62], "schatz2y"),
        "fed_funds": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.55, 1.55, 1.55], "fed_funds"),
        "ecb_rate": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [-0.50, -0.50, -0.50], "ecb_rate"),
        "dxy": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [96.0, 96.2, 96.5], "dxy"),
        "brent": _series(["2020-01-03", "2020-01-06"], [66.0, 68.0], "brent"),
    }
    df = build_daily_panel(series)
    assert pd.isna(df.loc["2020-01-02", "brent"])
    assert df.loc["2020-01-03", "brent"] == 66.0


def test_build_daily_panel_preserves_weekend_observations():
    # A Saturday Brent print must NOT be dropped by the business-day index.
    series = {
        "eurusd": _series(["2020-01-02", "2020-01-03"], [1.12, 1.13], "eurusd"),
        "ust10y": _series(["2020-01-02", "2020-01-03"], [1.90, 1.85], "ust10y"),
        "bund10y": _series(["2020-01-02", "2020-01-03"], [-0.20, -0.25], "bund10y"),
        "ust2y": _series(["2020-01-02", "2020-01-03"], [1.55, 1.52], "ust2y"),
        "schatz2y": _series(["2020-01-02", "2020-01-03"], [-0.60, -0.61], "schatz2y"),
        "fed_funds": _series(["2020-01-02", "2020-01-03"], [1.55, 1.55], "fed_funds"),
        "ecb_rate": _series(["2020-01-02", "2020-01-03"], [-0.50, -0.50], "ecb_rate"),
        "dxy": _series(["2020-01-02", "2020-01-03"], [96.0, 96.2], "dxy"),
        # 2020-01-04 is a Saturday
        "brent": _series(["2020-01-02", "2020-01-04"], [66.0, 67.0], "brent"),
    }
    df = build_daily_panel(series)
    assert pd.Timestamp("2020-01-04") in df.index
    assert df.loc["2020-01-04", "brent"] == 67.0


def test_build_monthly_panel_resamples_and_joins_inflation():
    daily_idx = pd.bdate_range("2020-01-01", "2020-02-28")
    daily = pd.DataFrame(
        {
            "eurusd": 1.10, "ust10y": 1.8, "bund10y": -0.2, "ust2y": 1.5,
            "schatz2y": -0.6, "dxy": 96.0, "brent": 60.0, "spread10y": 2.0, "spread2y": 2.1,
        },
        index=daily_idx,
    )
    daily.index.name = "date"
    series = {
        "us_cpi": _series(["2020-01-01", "2020-02-01"], [257.9, 258.7], "us_cpi"),
        "eu_hicp": _series(["2020-01-01", "2020-02-01"], [104.7, 105.0], "eu_hicp"),
    }
    monthly = build_monthly_panel(daily, series)
    assert list(monthly.index) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]
    assert monthly.loc["2020-01-31", "us_cpi"] == 257.9
    assert monthly.loc["2020-02-29", "eu_hicp"] == 105.0
    assert monthly.loc["2020-01-31", "eurusd"] == 1.10
