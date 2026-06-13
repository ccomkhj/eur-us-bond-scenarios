"""Registry of source series, grouped by provider.

FRED's CSV endpoint is unreachable from many networks (see ADR-0002), so every series
is sourced from a reachable, keyless provider instead:
  - ECB Data Portal  — EUR/USD, Bund/Schatz yields, ECB deposit rate, euro-area HICP
  - US Treasury      — US 2y & 10y par yields (official daily CSV)
  - NY Fed           — effective federal funds rate (the US policy rate)
  - Yahoo Finance    — broad USD index (DXY) and Brent crude
  - BLS              — US CPI (keyless public API)
The series *names* match what the rest of the pipeline + front-end expect.
"""

# ECB Data Portal: name -> (dataset/flow, series key). parse_ecb_csv reads TIME_PERIOD/OBS_VALUE.
ECB_SERIES: dict[str, tuple[str, str]] = {
    "eurusd": ("EXR", "D.USD.EUR.SP00.A"),                  # US$ per euro, daily
    "bund10y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),  # AAA euro-area 10y spot yield
    "schatz2y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"),  # AAA euro-area 2y spot yield
    "ecb_rate": ("FM", "B.U2.EUR.4F.KR.DFR.LEV"),           # ECB deposit facility rate (policy)
    "eu_hicp": ("ICP", "M.U2.N.000000.4.INX"),              # euro-area HICP index, monthly
}

# US Treasury daily par yield curve CSV: name -> column label in the CSV.
TREASURY_COLUMNS: dict[str, str] = {
    "ust2y": "2 Yr",
    "ust10y": "10 Yr",
}

# Yahoo Finance chart API: name -> symbol.
YAHOO_SYMBOLS: dict[str, str] = {
    "dxy": "DX-Y.NYB",  # ICE US Dollar Index
    "brent": "BZ=F",    # Brent crude front-month future
}

# BLS public API: name -> series id.
BLS_SERIES: dict[str, str] = {
    "us_cpi": "CUUR0000SA0",  # CPI for All Urban Consumers, all items, NSA index
}

# fed_funds comes from the NY Fed EFFR endpoint (a single fixed series, handled in fetch.py).

# History start year for the per-year Treasury / BLS pulls.
START_YEAR = 2015

# Which series form the daily panel vs are monthly-only.
DAILY_SERIES: list[str] = [
    "eurusd", "ust10y", "bund10y", "ust2y", "schatz2y", "fed_funds", "ecb_rate", "dxy", "brent",
]
MONTHLY_ONLY: list[str] = ["us_cpi", "eu_hicp"]

assert not (set(DAILY_SERIES) & set(MONTHLY_ONLY)), "a series cannot be both daily and monthly-only"

# Endpoint templates.
ECB_CSV_URL = "https://data-api.ecb.europa.eu/service/data/{flow}/{key}?format=csvdata"
NYFED_EFFR_URL = (
    "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json"
    "?startDate={start}&endDate={end}"
)
TREASURY_CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all"
    "?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
)
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=15y&interval=1d"
BLS_API_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
