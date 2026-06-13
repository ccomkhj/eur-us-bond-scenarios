"""Pure parsers that turn raw provider payloads into a clean pandas Series (no network).

Each returns a float Series indexed by a sorted `date` DatetimeIndex with NaNs dropped.
"""
import io
import json

import pandas as pd


def _arr(x):
    # Drop any existing pandas index so values bind to the new index POSITIONALLY
    # (passing an indexed Series as data would otherwise re-align and blank everything).
    return x.to_numpy() if isinstance(x, pd.Series) else x


def _clean(values, index, name: str) -> pd.Series:
    s = pd.Series(
        pd.to_numeric(_arr(values), errors="coerce"),
        index=pd.to_datetime(_arr(index)),
        name=name,
    )
    s.index.name = "date"
    return s.dropna().sort_index()


def parse_ecb_csv(text: str, name: str) -> pd.Series:
    """ECB SDMX csvdata: read the TIME_PERIOD and OBS_VALUE columns by name (column
    order varies by dataset, so never rely on position)."""
    df = pd.read_csv(io.StringIO(text))
    return _clean(df["OBS_VALUE"], df["TIME_PERIOD"], name)


def parse_nyfed_effr_json(text: str, name: str) -> pd.Series:
    """NY Fed reference-rates JSON: {"refRates": [{"effectiveDate", "percentRate", ...}]}."""
    rows = json.loads(text)["refRates"]
    return _clean(
        [r.get("percentRate") for r in rows],
        [r["effectiveDate"] for r in rows],
        name,
    )


def parse_treasury_csv(text: str, column: str, name: str) -> pd.Series:
    """US Treasury daily par-yield CSV: a `Date` column (MM/DD/YYYY) plus one column per
    maturity (e.g. "2 Yr", "10 Yr"). Extract the requested maturity column."""
    df = pd.read_csv(io.StringIO(text))
    return _clean(df[column], df["Date"], name)


def parse_yahoo_chart_json(text: str, name: str) -> pd.Series:
    """Yahoo Finance chart JSON: chart.result[0] has unix `timestamp[]` and
    indicators.quote[0].close[]. Timestamps are normalised to the calendar day."""
    res = json.loads(text)["chart"]["result"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s").normalize()
    return _clean(res["indicators"]["quote"][0]["close"], idx, name)


def parse_bls_json(text: str, name: str) -> pd.Series:
    """BLS timeseries JSON: Results.series[0].data[] with {year, period:"M01".."M12",
    value}. Skip the annual-average row ("M13"); missing values arrive as "-"."""
    data = json.loads(text)["Results"]["series"][0]["data"]
    recs = [(f"{d['year']}-{d['period'][1:]}-01", d["value"]) for d in data if d["period"] != "M13"]
    return _clean([v for _, v in recs], [dt for dt, _ in recs], name)
