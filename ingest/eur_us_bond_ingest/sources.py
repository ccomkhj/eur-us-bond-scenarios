"""Registry of source series and their download URLs."""

# FRED series downloaded as CSV (no API key needed via fredgraph.csv).
FRED_SERIES: dict[str, str] = {
    "eurusd": "DEXUSEU",        # US$ per euro, daily, since 1999
    "ust10y": "DGS10",          # US 10y Treasury constant-maturity yield, daily
    "ust2y": "DGS2",            # US 2y Treasury constant-maturity yield, daily
    "dxy": "DTWEXBGS",          # Nominal Broad US Dollar Index, daily (broad-USD proxy)
    "brent": "DCOILBRENTEU",    # Crude Oil Brent Europe, daily, since 1987
    "us_cpi": "CPIAUCSL",       # US CPI all-urban, SA, monthly
    "eu_hicp": "CP0000EZCCM086NEST",  # Euro-area HICP, consolidated composition, monthly
}

# ECB Data Portal daily AAA euro-area government bond spot yields (Bund/Schatz proxy).
ECB_SERIES: dict[str, str] = {
    "bund10y": "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y",
    "schatz2y": "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y",
}

# Which series form the daily panel vs are monthly-only.
DAILY_SERIES: list[str] = ["eurusd", "ust10y", "bund10y", "ust2y", "schatz2y", "dxy", "brent"]
MONTHLY_ONLY: list[str] = ["us_cpi", "eu_hicp"]

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
ECB_CSV_URL = "https://data-api.ecb.europa.eu/service/data/YC/{key}?format=csvdata"
