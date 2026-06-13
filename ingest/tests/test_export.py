import json
import pandas as pd
from eur_us_bond_ingest.export import df_to_columnar, write_outputs


def test_df_to_columnar_emits_dates_and_null_for_nan():
    df = pd.DataFrame(
        {"eurusd": [1.10, float("nan")], "spread10y": [2.0, 2.1]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    df.index.name = "date"
    out = df_to_columnar(df)
    assert out["dates"] == ["2020-01-02", "2020-01-03"]
    assert out["series"]["eurusd"] == [1.10, None]
    assert out["series"]["spread10y"] == [2.0, 2.1]


def test_write_outputs_writes_parquet_and_json(tmp_path):
    df = pd.DataFrame({"eurusd": [1.10, 1.11]}, index=pd.to_datetime(["2020-01-02", "2020-01-03"]))
    df.index.name = "date"
    write_outputs(df, df, tmp_path, default_start="2021-01-01")
    assert (tmp_path / "daily.parquet").exists()
    assert (tmp_path / "monthly.parquet").exists()
    payload = json.loads((tmp_path / "data.json").read_text())
    assert payload["meta"]["default_start"] == "2021-01-01"
    assert payload["daily"]["series"]["eurusd"] == [1.10, 1.11]
    assert "monthly" in payload
    rt = pd.read_parquet(tmp_path / "daily.parquet")
    assert list(rt.index) == [pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-03")]
