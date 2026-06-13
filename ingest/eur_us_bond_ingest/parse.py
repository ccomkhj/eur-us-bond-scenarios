"""Pure parsers that turn raw CSV text into a clean pandas Series (no network)."""
import io
import pandas as pd


def parse_fred_csv(text: str, name: str) -> pd.Series:
    """fredgraph.csv: first column is the date, second is the value; '.' means missing."""
    df = pd.read_csv(io.StringIO(text), na_values=["."])
    date_col, value_col = df.columns[0], df.columns[1]
    s = pd.Series(
        pd.to_numeric(df[value_col], errors="coerce").to_numpy(),
        index=pd.to_datetime(df[date_col]),
        name=name,
    )
    s.index.name = "date"
    return s.dropna().sort_index()


def parse_ecb_csv(text: str, name: str) -> pd.Series:
    """ECB SDMX csvdata: read the TIME_PERIOD and OBS_VALUE columns by name."""
    df = pd.read_csv(io.StringIO(text))
    s = pd.Series(
        pd.to_numeric(df["OBS_VALUE"], errors="coerce").to_numpy(),
        index=pd.to_datetime(df["TIME_PERIOD"]),
        name=name,
    )
    s.index.name = "date"
    return s.dropna().sort_index()
