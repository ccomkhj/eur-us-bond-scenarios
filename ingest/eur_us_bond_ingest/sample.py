"""Generate a synthetic but plausible dataset for OFFLINE front-end dev / CI.

This is NOT real market data. It exists so the static front-end can be developed
and verified without network access to FRED/ECB. For real data, run the CLI:
`python -m eur_us_bond_ingest.cli`.

It reuses the real pipeline (build_daily_panel / build_monthly_panel / df_to_columnar)
so the sample exercises the same code paths the real ingest does, and writes only
`web/public/data.json` — it never touches the canonical `data/` parquet panels.
"""
import json
from pathlib import Path

import pandas as pd

from .align import build_daily_panel, build_monthly_panel
from .export import df_to_columnar

WEB_PUBLIC = Path(__file__).resolve().parents[2] / "web" / "public"


def _walk(n: int, start: float, step: float, seed: int) -> list[float]:
    """Deterministic pseudo-random walk (a self-contained LCG — no global RNG state,
    so the sample is byte-stable across runs)."""
    values: list[float] = []
    x = start
    state = seed
    for _ in range(n):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        x += step * ((state / 0x7FFFFFFF) - 0.5)
        values.append(round(x, 4))
    return values


def make_sample(start: str = "2015-01-01", end: str = "2025-01-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    bdays = pd.bdate_range(start, end)

    def series(name: str, s0: float, step: float, seed: int) -> pd.Series:
        s = pd.Series(_walk(len(bdays), s0, step, seed), index=bdays, name=name)
        s.index.name = "date"
        return s

    raw: dict[str, pd.Series] = {
        "eurusd": series("eurusd", 1.12, 0.004, 1),
        "ust10y": series("ust10y", 2.0, 0.03, 2),
        "bund10y": series("bund10y", 0.5, 0.03, 3),
        "ust2y": series("ust2y", 1.5, 0.03, 4),
        "schatz2y": series("schatz2y", 0.0, 0.03, 5),
        "dxy": series("dxy", 95.0, 0.2, 6),
        "brent": series("brent", 70.0, 1.0, 7),
    }
    months = pd.date_range(start, end, freq="MS")
    for name, s0, step, seed in [("us_cpi", 240.0, 0.4, 8), ("eu_hicp", 100.0, 0.3, 9)]:
        s = pd.Series(_walk(len(months), s0, step, seed), index=months, name=name)
        s.index.name = "date"
        raw[name] = s

    daily = build_daily_panel(raw)
    monthly = build_monthly_panel(daily, raw)
    return daily, monthly


def main() -> None:
    daily, monthly = make_sample()
    WEB_PUBLIC.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {"default_start": "2021-01-01"},
        "daily": df_to_columnar(daily),
        "monthly": df_to_columnar(monthly),
    }
    (WEB_PUBLIC / "data.json").write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote SAMPLE (synthetic, not real market data) -> {WEB_PUBLIC / 'data.json'}")


if __name__ == "__main__":
    main()
