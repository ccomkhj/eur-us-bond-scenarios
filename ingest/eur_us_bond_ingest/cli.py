"""Entry point: fetch -> align -> export. Run with `python -m eur_us_bond_ingest.cli`."""
from pathlib import Path

from .align import build_daily_panel, build_monthly_panel
from .export import write_outputs
from .fetch import fetch_all

# Repo-root /data, resolved relative to this file (ingest/eur_us_bond_ingest/cli.py).
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main() -> None:
    print("Fetching series from FRED + ECB ...")
    series = fetch_all()
    for name, s in series.items():
        print(f"  {name:10s} {len(s):6d} obs  {s.index.min().date()} -> {s.index.max().date()}")
    daily = build_daily_panel(series)
    monthly = build_monthly_panel(daily, series)
    write_outputs(daily, monthly, DATA_DIR)
    print(f"Wrote daily.parquet ({len(daily)} rows), monthly.parquet ({len(monthly)} rows), data.json -> {DATA_DIR}")


if __name__ == "__main__":
    main()
