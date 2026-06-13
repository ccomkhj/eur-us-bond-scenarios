import json

import pandas as pd
from eur_us_bond_ingest.parse import (
    parse_bls_json,
    parse_ecb_csv,
    parse_nyfed_effr_json,
    parse_treasury_csv,
    parse_yahoo_chart_json,
)


def test_parse_ecb_csv_reads_time_period_and_obs_value_by_name():
    # Column ORDER differs across ECB datasets; the parser must select by name.
    text = (
        "KEY,FREQ,OBS_STATUS,TIME_PERIOD,OBS_VALUE,TITLE\n"
        "EXR...,D,A,2020-01-02,1.117,Rate\n"
        "EXR...,D,A,2020-01-03,1.120,Rate\n"
    )
    s = parse_ecb_csv(text, "eurusd")
    assert s.name == "eurusd"
    assert s.loc[pd.Timestamp("2020-01-03")] == 1.120
    assert s.index.name == "date"


def test_parse_nyfed_effr_json_reads_date_and_rate_and_sorts():
    text = json.dumps(
        {"refRates": [
            {"effectiveDate": "2020-01-06", "type": "EFFR", "percentRate": 1.55},
            {"effectiveDate": "2020-01-02", "type": "EFFR", "percentRate": 1.54},
        ]}
    )
    s = parse_nyfed_effr_json(text, "fed_funds")
    assert s.name == "fed_funds"
    assert list(s.index) == [pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-06")]
    assert s.loc[pd.Timestamp("2020-01-06")] == 1.55


def test_parse_treasury_csv_extracts_named_maturity_column():
    text = (
        'Date,"1 Mo","2 Yr","10 Yr"\n'
        "01/02/2020,1.53,1.58,1.88\n"
        "01/03/2020,1.52,1.55,1.81\n"
    )
    s10 = parse_treasury_csv(text, "10 Yr", "ust10y")
    s2 = parse_treasury_csv(text, "2 Yr", "ust2y")
    assert s10.loc[pd.Timestamp("2020-01-02")] == 1.88
    assert s2.loc[pd.Timestamp("2020-01-03")] == 1.55
    assert s10.index.name == "date"


def test_parse_yahoo_chart_json_uses_timestamps_and_close():
    # 2020-01-02 and 2020-01-03 (unix seconds, market open); normalised to the day.
    text = json.dumps(
        {"chart": {"result": [
            {"timestamp": [1577966400, 1578052800],
             "indicators": {"quote": [{"close": [96.0, 96.5]}]}}
        ]}}
    )
    s = parse_yahoo_chart_json(text, "dxy")
    assert s.name == "dxy"
    assert s.iloc[0] == 96.0 and s.iloc[1] == 96.5
    assert s.index.normalize().equals(s.index)  # already day-aligned


def test_parse_bls_json_skips_annual_average_and_missing():
    text = json.dumps(
        {"Results": {"series": [{"data": [
            {"year": "2020", "period": "M13", "value": "258.0"},   # annual avg -> skip
            {"year": "2020", "period": "M02", "value": "258.7"},
            {"year": "2020", "period": "M01", "value": "257.9"},
            {"year": "2020", "period": "M03", "value": "-"},        # missing -> dropped
        ]}]}}
    )
    s = parse_bls_json(text, "us_cpi")
    assert list(s.index) == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01")]
    assert s.loc[pd.Timestamp("2020-02-01")] == 258.7
