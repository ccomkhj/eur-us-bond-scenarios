"""Thin network layer: download raw payloads from each provider, delegate to pure parsers."""
from datetime import date
from urllib.parse import quote

import pandas as pd
import requests

from .parse import (
    parse_bls_json,
    parse_ecb_csv,
    parse_nyfed_effr_json,
    parse_treasury_csv,
    parse_yahoo_chart_json,
)
from .sources import (
    BLS_API_URL,
    BLS_SERIES,
    ECB_CSV_URL,
    ECB_SERIES,
    NYFED_EFFR_URL,
    START_YEAR,
    TREASURY_COLUMNS,
    TREASURY_CSV_URL,
    YAHOO_CHART_URL,
    YAHOO_SYMBOLS,
)

# A browser-like UA: some providers (Yahoo, Treasury) reject default library agents.
_HEADERS = {"User-Agent": "Mozilla/5.0 (research; eur-us-bond-scenarios)"}


def _get(url: str) -> str:
    resp = requests.get(url, headers=_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def _post_json(url: str, payload: dict) -> str:
    resp = requests.post(url, json=payload, headers=_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def fetch_all() -> dict[str, pd.Series]:
    """Fetch every registered series from its provider and return {name: Series}."""
    today = date.today()
    series: dict[str, pd.Series] = {}

    # ECB Data Portal (EUR/USD, Bund/Schatz yields, ECB rate, HICP).
    for name, (flow, key) in ECB_SERIES.items():
        series[name] = parse_ecb_csv(_get(ECB_CSV_URL.format(flow=flow, key=key)), name)

    # NY Fed: effective federal funds rate (US policy rate).
    effr_url = NYFED_EFFR_URL.format(start=f"{START_YEAR}-01-01", end=today.isoformat())
    series["fed_funds"] = parse_nyfed_effr_json(_get(effr_url), "fed_funds")

    # US Treasury par yields: one CSV per year, both maturities extracted per pull.
    years = range(START_YEAR, today.year + 1)
    csv_by_year = {y: _get(TREASURY_CSV_URL.format(year=y)) for y in years}
    for name, column in TREASURY_COLUMNS.items():
        parts = [parse_treasury_csv(csv_by_year[y], column, name) for y in years]
        series[name] = pd.concat(parts).sort_index()

    # Yahoo Finance (DXY, Brent).
    for name, symbol in YAHOO_SYMBOLS.items():
        series[name] = parse_yahoo_chart_json(_get(YAHOO_CHART_URL.format(symbol=quote(symbol))), name)

    # BLS (US CPI). The keyless v1 API caps each request at 10 years, so take the most recent.
    bls_start = max(START_YEAR, today.year - 9)
    for name, series_id in BLS_SERIES.items():
        payload = {"seriesid": [series_id], "startyear": str(bls_start), "endyear": str(today.year)}
        series[name] = parse_bls_json(_post_json(BLS_API_URL, payload), name)

    return series
