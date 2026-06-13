"""Build the daily and monthly panels from per-series data."""
import pandas as pd

from .sources import DAILY_SERIES, MONTHLY_ONLY


def build_daily_panel(series: dict[str, pd.Series]) -> pd.DataFrame:
    """Reindex daily series to a common index — the business-day grid augmented
    with any observation dates that fall outside it (e.g. a weekend Brent print)
    so no real observation is ever dropped — forward-fill gaps (holidays), and add
    the derived yield spreads. Leading NaNs (before a series' first observation)
    are left as NaN — we never backfill."""
    df = pd.DataFrame({k: series[k] for k in DAILY_SERIES})
    idx = pd.bdate_range(df.index.min(), df.index.max()).union(df.index)
    df = df.reindex(idx).ffill()
    df["spread10y"] = df["ust10y"] - df["bund10y"]
    df["spread2y"] = df["ust2y"] - df["schatz2y"]
    df.index.name = "date"
    return df


def build_monthly_panel(daily: pd.DataFrame, series: dict[str, pd.Series]) -> pd.DataFrame:
    """Resample the daily panel to month-end (last value) and join the
    monthly-only inflation series, aligned to month-end timestamps."""
    monthly = daily.resample("ME").last()
    for key in MONTHLY_ONLY:
        s = series[key].copy()
        s.index = s.index.to_period("M").to_timestamp("M")
        monthly[key] = s.reindex(monthly.index)
    monthly.index.name = "date"
    return monthly
