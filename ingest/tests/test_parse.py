import pandas as pd
from eur_us_bond_ingest.parse import parse_fred_csv, parse_ecb_csv


def test_parse_fred_csv_handles_dot_missing_values():
    text = "observation_date,DGS10\n2020-01-02,1.88\n2020-01-03,.\n2020-01-06,1.81\n"
    s = parse_fred_csv(text, "ust10y")
    assert s.name == "ust10y"
    assert list(s.index) == [pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-06")]
    assert s.loc[pd.Timestamp("2020-01-02")] == 1.88
    assert s.index.name == "date"


def test_parse_ecb_csv_reads_time_period_and_obs_value():
    text = (
        "KEY,FREQ,TIME_PERIOD,OBS_VALUE,TITLE\n"
        "YC...SR_10Y,B,2020-01-02,1.20,Yield\n"
        "YC...SR_10Y,B,2020-01-03,1.25,Yield\n"
    )
    s = parse_ecb_csv(text, "bund10y")
    assert s.name == "bund10y"
    assert s.loc[pd.Timestamp("2020-01-03")] == 1.25
    assert s.index.name == "date"
