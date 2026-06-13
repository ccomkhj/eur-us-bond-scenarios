"""Thin network layer: download raw CSV text, then delegate to pure parsers."""
import pandas as pd
import requests

from .parse import parse_ecb_csv, parse_fred_csv
from .sources import ECB_CSV_URL, ECB_SERIES, FRED_CSV_URL, FRED_SERIES

_HEADERS = {"User-Agent": "eur-us-bond-scenarios/0.1 (research)"}


def _get(url: str) -> str:
    resp = requests.get(url, headers=_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def fetch_all() -> dict[str, pd.Series]:
    """Fetch every registered series and return {name: Series}."""
    series: dict[str, pd.Series] = {}
    for name, series_id in FRED_SERIES.items():
        text = _get(FRED_CSV_URL.format(series_id=series_id))
        series[name] = parse_fred_csv(text, name)
    for name, key in ECB_SERIES.items():
        text = _get(ECB_CSV_URL.format(key=key))
        series[name] = parse_ecb_csv(text, name)
    return series
