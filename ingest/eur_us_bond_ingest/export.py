"""Write the canonical parquet panels and the front-end's columnar data.json."""
import json
from pathlib import Path

import pandas as pd


def df_to_columnar(df: pd.DataFrame) -> dict:
    """Compact columnar shape: a shared `dates` array + parallel value arrays.
    NaN becomes JSON null so the front-end can skip missing points."""
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "series": {
            col: [None if pd.isna(v) else float(v) for v in df[col]]
            for col in df.columns
        },
    }


def write_outputs(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    out_dir: Path,
    default_start: str = "2021-01-01",
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out_dir / "daily.parquet")
    monthly.to_parquet(out_dir / "monthly.parquet")
    payload = {
        "meta": {"default_start": default_start},
        "daily": df_to_columnar(daily),
        "monthly": df_to_columnar(monthly),
    }
    # No generation timestamp: keeps committed JSON diffs clean across re-runs.
    (out_dir / "data.json").write_text(json.dumps(payload, separators=(",", ":")))
