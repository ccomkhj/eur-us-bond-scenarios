# EUR/US Bond Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the quantitative timeseries companion to `eur-usd-risk-scenarios` — ingest EUR/USD, US/EU yields, DXY, Brent, and inflation into committed parquet/JSON, then a static TypeScript app that plots them and computes correlation / lead-lag client-side.

**Architecture:** Python (build-time) fetches FRED + ECB series, aligns them into a daily and a monthly panel, and writes `data/daily.parquet`, `data/monthly.parquet`, and `data/data.json`. A static Vite + TypeScript front-end loads `data.json` and computes rolling correlation and lead-lag (cross-correlation) **in the browser**. No server runs at app time. See `docs/adr/0001-python-ingest-static-ts-viz.md` and `CONTEXT.md`.

**Tech Stack:** Python 3.12 (uv, pandas, pyarrow, requests, pytest) · TypeScript (Vite, Plotly.js, vitest)

**Key conventions (match sibling repo `../eur-usd-risk-scenarios`):** ESM modules, strict TypeScript, vitest. Stats default to **changes/log-returns**, never raw levels (avoids spurious trend correlation). Inflation correlation is monthly-only.

---

## File Structure

```
eur-us-bond-scenarios/
  CONTEXT.md                         # (exists) glossary + decisions
  docs/adr/0001-...md                # (exists) runtime-split ADR
  Makefile                           # `make data` orchestrates ingest + copy
  README.md
  ingest/                            # Python — Phase 0
    pyproject.toml
    eur_us_bond_ingest/
      __init__.py
      sources.py                     # series-id registry + URLs
      parse.py                       # pure CSV parsers (FRED, ECB)
      fetch.py                       # network fetch (thin)
      align.py                       # daily + monthly panel builders
      export.py                      # parquet + data.json writers
      cli.py                         # `python -m eur_us_bond_ingest.cli`
    tests/
      test_parse.py
      test_align.py
      test_export.py
  data/                              # committed artifacts
    daily.parquet  monthly.parquet  data.json
  web/                               # TypeScript — Phase 1
    package.json  tsconfig.json  vite.config.ts  index.html
    public/data.json                 # copied from ../data by `make data`
    src/
      main.ts                        # wires panels + UI
      data.ts                        # typed loader for data.json
      stats.ts                       # diffs, log-returns, pearson, rollingCorr, crossCorr
      charts.ts                      # Plotly render helpers (overlay, leadlag, rollingcorr)
      declarations.d.ts              # `declare module 'plotly.js-dist-min'`
    test/
      stats.test.ts
```

---

## PHASE 0 — Python ingestion

### Task 1: Python project scaffold

**Files:**
- Create: `ingest/pyproject.toml`
- Create: `ingest/eur_us_bond_ingest/__init__.py`
- Create: `ingest/eur_us_bond_ingest/sources.py`
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`** (data/ is intentionally NOT ignored — artifacts are committed)

```
# Python
__pycache__/
*.pyc
.venv/
ingest/.venv/
# Node
node_modules/
web/dist/
# OS / editor
.DS_Store
.idea/
.vscode/
*.swp
```

- [ ] **Step 2: Create `ingest/pyproject.toml`**

```toml
[project]
name = "eur-us-bond-ingest"
version = "0.1.0"
description = "Ingest FRED + ECB macro series into aligned parquet/JSON panels."
requires-python = ">=3.12"
dependencies = ["pandas>=2.2", "pyarrow>=16", "requests>=2.32"]

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["eur_us_bond_ingest"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `ingest/eur_us_bond_ingest/__init__.py`** (empty file)

```python
```

- [ ] **Step 4: Create `ingest/eur_us_bond_ingest/sources.py`** (the series registry — the single source of truth for what we fetch)

```python
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
```

- [ ] **Step 5: Install dependencies**

Run: `uv sync --directory ingest`
Expected: resolves and installs pandas, pyarrow, requests, pytest.

- [ ] **Step 6: Commit**

```bash
git add .gitignore ingest/pyproject.toml ingest/eur_us_bond_ingest/__init__.py ingest/eur_us_bond_ingest/sources.py ingest/uv.lock
git commit -m "chore: scaffold python ingest package + series registry"
```

---

### Task 2: CSV parsers (FRED + ECB) — pure functions

**Files:**
- Create: `ingest/eur_us_bond_ingest/parse.py`
- Test: `ingest/tests/test_parse.py`

- [ ] **Step 1: Write the failing test**

```python
# ingest/tests/test_parse.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory ingest pytest tests/test_parse.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eur_us_bond_ingest.parse'`

- [ ] **Step 3: Write minimal implementation**

```python
# ingest/eur_us_bond_ingest/parse.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory ingest pytest tests/test_parse.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add ingest/eur_us_bond_ingest/parse.py ingest/tests/test_parse.py
git commit -m "feat(ingest): pure FRED + ECB CSV parsers"
```

---

### Task 3: Daily panel builder (alignment + derived spreads)

**Files:**
- Create: `ingest/eur_us_bond_ingest/align.py`
- Test: `ingest/tests/test_align.py`

- [ ] **Step 1: Write the failing test**

```python
# ingest/tests/test_align.py
import pandas as pd
from eur_us_bond_ingest.align import build_daily_panel


def _series(dates, values, name):
    s = pd.Series(values, index=pd.to_datetime(dates), name=name)
    s.index.name = "date"
    return s


def test_build_daily_panel_reindexes_to_business_days_ffills_and_adds_spreads():
    # 2020-01-01 is a Wednesday holiday; business days start 2020-01-02 (Thu).
    series = {
        "eurusd": _series(["2020-01-02", "2020-01-06"], [1.12, 1.13], "eurusd"),
        "ust10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [1.90, 1.85, 1.80], "ust10y"),
        "bund10y": _series(["2020-01-02", "2020-01-03", "2020-01-06"], [-0.20, -0.25, -0.30], "bund10y"),
        "ust2y": _series(["2020-01-02", "2020-01-06"], [1.55, 1.50], "ust2y"),
        "schatz2y": _series(["2020-01-02", "2020-01-06"], [-0.60, -0.62], "schatz2y"),
        "dxy": _series(["2020-01-02", "2020-01-06"], [96.0, 96.5], "dxy"),
        "brent": _series(["2020-01-02", "2020-01-06"], [66.0, 68.0], "brent"),
    }
    df = build_daily_panel(series)

    # Business-day index 2020-01-02..2020-01-06 (Thu, Fri, Mon).
    assert list(df.index) == [pd.Timestamp(d) for d in ["2020-01-02", "2020-01-03", "2020-01-06"]]
    # eurusd had no 01-03 obs -> forward-filled from 01-02.
    assert df.loc["2020-01-03", "eurusd"] == 1.12
    # Derived spreads.
    assert df.loc["2020-01-02", "spread10y"] == 1.90 - (-0.20)
    assert df.loc["2020-01-06", "spread2y"] == 1.50 - (-0.62)
    assert df.index.name == "date"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory ingest pytest tests/test_align.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eur_us_bond_ingest.align'`

- [ ] **Step 3: Write minimal implementation**

```python
# ingest/eur_us_bond_ingest/align.py
"""Build the daily and monthly panels from per-series data."""
import pandas as pd

from .sources import DAILY_SERIES, MONTHLY_ONLY


def build_daily_panel(series: dict[str, pd.Series]) -> pd.DataFrame:
    """Reindex daily series to a common business-day index, forward-fill gaps
    (holidays), and add the derived yield spreads. Leading NaNs (before a series'
    first observation) are left as NaN — we never backfill."""
    df = pd.DataFrame({k: series[k] for k in DAILY_SERIES})
    idx = pd.bdate_range(df.index.min(), df.index.max())
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory ingest pytest tests/test_align.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add ingest/eur_us_bond_ingest/align.py ingest/tests/test_align.py
git commit -m "feat(ingest): daily panel builder with business-day alignment + spreads"
```

---

### Task 4: Monthly panel builder

**Files:**
- Modify: `ingest/tests/test_align.py` (add a test; `build_monthly_panel` already written in Task 3)

- [ ] **Step 1: Add the failing test**

```python
# append to ingest/tests/test_align.py
from eur_us_bond_ingest.align import build_monthly_panel


def test_build_monthly_panel_resamples_and_joins_inflation():
    daily_idx = pd.bdate_range("2020-01-01", "2020-02-28")
    daily = pd.DataFrame(
        {
            "eurusd": 1.10,
            "ust10y": 1.8,
            "bund10y": -0.2,
            "ust2y": 1.5,
            "schatz2y": -0.6,
            "dxy": 96.0,
            "brent": 60.0,
            "spread10y": 2.0,
            "spread2y": 2.1,
        },
        index=daily_idx,
    )
    daily.index.name = "date"
    series = {
        "us_cpi": _series(["2020-01-01", "2020-02-01"], [257.9, 258.7], "us_cpi"),
        "eu_hicp": _series(["2020-01-01", "2020-02-01"], [104.7, 105.0], "eu_hicp"),
    }
    monthly = build_monthly_panel(daily, series)

    assert list(monthly.index) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]
    assert monthly.loc["2020-01-31", "us_cpi"] == 257.9
    assert monthly.loc["2020-02-29", "eu_hicp"] == 105.0
    assert monthly.loc["2020-01-31", "eurusd"] == 1.10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory ingest pytest tests/test_align.py::test_build_monthly_panel_resamples_and_joins_inflation -v`
Expected: PASS immediately IF Task 3 implemented `build_monthly_panel` correctly. If it FAILS on the month-end join, fix `build_monthly_panel` until this test passes. (This test exists to lock the monthly behavior.)

- [ ] **Step 3: Commit**

```bash
git add ingest/tests/test_align.py
git commit -m "test(ingest): lock monthly panel resample + inflation join"
```

---

### Task 5: Exporters (parquet + columnar data.json)

**Files:**
- Create: `ingest/eur_us_bond_ingest/export.py`
- Test: `ingest/tests/test_export.py`

- [ ] **Step 1: Write the failing test**

```python
# ingest/tests/test_export.py
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
    # parquet round-trips with the date index.
    rt = pd.read_parquet(tmp_path / "daily.parquet")
    assert list(rt.index) == [pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-03")]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory ingest pytest tests/test_export.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'eur_us_bond_ingest.export'`

- [ ] **Step 3: Write minimal implementation**

```python
# ingest/eur_us_bond_ingest/export.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --directory ingest pytest tests/test_export.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add ingest/eur_us_bond_ingest/export.py ingest/tests/test_export.py
git commit -m "feat(ingest): parquet + columnar data.json exporters"
```

---

### Task 6: Network fetch + CLI (integration — produces the committed data)

**Files:**
- Create: `ingest/eur_us_bond_ingest/fetch.py`
- Create: `ingest/eur_us_bond_ingest/cli.py`

Network I/O is not unit-tested (it hits live endpoints); correctness is verified by running it and inspecting the output.

- [ ] **Step 1: Write `ingest/eur_us_bond_ingest/fetch.py`**

```python
# ingest/eur_us_bond_ingest/fetch.py
"""Thin network layer: download raw CSV text, then delegate to pure parsers."""
import pandas as pd
import requests

from .parse import parse_ecb_csv, parse_fred_csv
from .sources import ECB_CSV_URL, ECB_SERIES, FRED_CSV_URL, FRED_SERIES

_HEADERS = {"User-Agent": "eur-us-bond-scenarios/0.1 (research)"}


def _get(url: str) -> str:
    resp = requests.get(url, headers=_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def fetch_all() -> dict[str, pd.Series]:
    """Fetch every registered series and return {name: Series}."""
    series: dict[str, pd.Series] = {}
    for name, series_id in FRED_SERIES.items():
        text = _get(FRED_CSV_URL.format(series_id=series_id))
        series[name] = parse_fred_csv(text, name)
    for name, key in ECB_SERIES.items():
        text = _get(ECB_CSV_URL.format(key=key))
        series[name] = parse_ecb_csv(text, name)
    return series
```

- [ ] **Step 2: Write `ingest/eur_us_bond_ingest/cli.py`**

```python
# ingest/eur_us_bond_ingest/cli.py
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
```

- [ ] **Step 3: Run the ingester for real**

Run: `uv run --directory ingest python -m eur_us_bond_ingest.cli`
Expected: prints per-series obs counts and date ranges (e.g. `eurusd` from ~1999, `bund10y` from ~2004), then writes the three files into `data/`. If a FRED id 404s, re-check it against `sources.py`; if the ECB URL fails, confirm the `YC` flow + key in `ECB_CSV_URL`.

- [ ] **Step 4: Sanity-check the output**

Run: `uv run --directory ingest python -c "import pandas as pd; d=pd.read_parquet('data/daily.parquet'); print(d.columns.tolist()); print(d.tail(3))"`
Expected: columns include `eurusd, ust10y, bund10y, ust2y, schatz2y, dxy, brent, spread10y, spread2y`; recent rows show plausible values (EUR/USD ~1.0–1.2, spread10y a couple of percentage points).

- [ ] **Step 5: Commit code + data**

```bash
git add ingest/eur_us_bond_ingest/fetch.py ingest/eur_us_bond_ingest/cli.py data/daily.parquet data/monthly.parquet data/data.json
git commit -m "feat(ingest): network fetch + CLI; commit first data panels"
```

---

## PHASE 1 — TypeScript static front-end

### Task 7: Web project scaffold

**Files:**
- Create: `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`, `web/index.html`, `web/src/declarations.d.ts`, `web/src/main.ts`
- Create: `Makefile`

- [ ] **Step 1: Create `web/package.json`**

```json
{
  "name": "eur-us-bond-web",
  "version": "0.1.0",
  "type": "module",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "plotly.js-dist-min": "^2.35.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create `web/tsconfig.json`** (mirrors the sibling repo's strict config, adds DOM)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src", "test"]
}
```

- [ ] **Step 3: Create `web/vite.config.ts`**

```ts
import { defineConfig } from 'vite';

export default defineConfig({
  test: { environment: 'node' },
});
```

- [ ] **Step 4: Create `web/src/declarations.d.ts`** (plotly.js-dist-min ships no types)

```ts
declare module 'plotly.js-dist-min';
```

- [ ] **Step 5: Create `web/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>EUR/US Bond Scenarios</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem; }
      .controls { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; }
      .chart { width: 100%; height: 380px; }
      .note { color: #b45309; font-size: 0.85rem; }
    </style>
  </head>
  <body>
    <h1>EUR/US Bond Scenarios</h1>
    <div class="controls">
      <label>Mode:
        <select id="mode"><option value="changes">changes (honest)</option><option value="levels">levels</option></select>
      </label>
      <label>Start: <input id="start" type="date" /></label>
      <label>Rolling window (days): <input id="window" type="range" min="20" max="250" value="90" /><span id="windowVal">90</span></label>
      <label>Max lag (days): <input id="maxlag" type="range" min="10" max="120" value="60" /><span id="maxlagVal">60</span></label>
      <span id="warn" class="note"></span>
    </div>
    <div id="overlay" class="chart"></div>
    <div id="leadlag" class="chart"></div>
    <div id="rollcorr" class="chart"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: Create `web/src/main.ts`** (placeholder; replaced in Task 12)

```ts
console.log('eur-us-bond-web booting');
```

- [ ] **Step 7: Create root `Makefile`**

```make
.PHONY: data web-install dev

# Refresh data: run the Python ingester, then copy data.json where Vite serves it.
data:
	uv run --directory ingest python -m eur_us_bond_ingest.cli
	mkdir -p web/public
	cp data/data.json web/public/data.json

web-install:
	cd web && npm install

dev:
	cd web && npm run dev
```

- [ ] **Step 8: Install + copy data into place**

Run: `make web-install && mkdir -p web/public && cp data/data.json web/public/data.json`
Expected: node_modules populated; `web/public/data.json` exists.

- [ ] **Step 9: Commit**

```bash
git add web/package.json web/tsconfig.json web/vite.config.ts web/index.html web/src/declarations.d.ts web/src/main.ts web/package-lock.json Makefile web/public/data.json
git commit -m "chore(web): scaffold vite + ts front-end; wire make data"
```

---

### Task 8: Stats — transforms (diffs, log-returns)

**Files:**
- Create: `web/src/stats.ts`
- Test: `web/test/stats.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// web/test/stats.test.ts
import { describe, it, expect } from 'vitest';
import { diffs, logReturns } from '../src/stats';

describe('transforms', () => {
  it('diffs returns first-difference with leading null and null-on-gap', () => {
    expect(diffs([1, 3, null, 4])).toEqual([null, 2, null, null]);
  });

  it('logReturns returns log ratio with leading null', () => {
    const r = logReturns([100, 110]);
    expect(r[0]).toBeNull();
    expect(r[1]).toBeCloseTo(Math.log(110 / 100), 10);
  });

  it('logReturns is null when a value is missing or non-positive', () => {
    expect(logReturns([null, 110])[1]).toBeNull();
    expect(logReturns([0, 110])[1]).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot resolve `../src/stats`.

- [ ] **Step 3: Write minimal implementation**

```ts
// web/src/stats.ts
export type Num = number | null;

/** First difference. Leading element is null; any gap (null on either side) yields null. */
export function diffs(xs: Num[]): Num[] {
  const out: Num[] = [null];
  for (let i = 1; i < xs.length; i++) {
    const a = xs[i - 1];
    const b = xs[i];
    out.push(a != null && b != null ? b - a : null);
  }
  return out;
}

/** Log returns. Leading element null; null when either value is missing or non-positive. */
export function logReturns(xs: Num[]): Num[] {
  const out: Num[] = [null];
  for (let i = 1; i < xs.length; i++) {
    const a = xs[i - 1];
    const b = xs[i];
    out.push(a != null && b != null && a > 0 && b > 0 ? Math.log(b / a) : null);
  }
  return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add web/src/stats.ts web/test/stats.test.ts
git commit -m "feat(web): diffs + logReturns transforms"
```

---

### Task 9: Stats — Pearson + rolling correlation

**Files:**
- Modify: `web/src/stats.ts`
- Modify: `web/test/stats.test.ts`

- [ ] **Step 1: Add the failing test**

```ts
// append to web/test/stats.test.ts
import { pearson, rollingCorr } from '../src/stats';

describe('correlation', () => {
  it('pearson is 1 for a perfect positive linear relation', () => {
    expect(pearson([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1, 10);
  });

  it('pearson drops pairs with a null on either side', () => {
    // Effective pairs: (1,2),(3,6) -> still perfectly correlated.
    expect(pearson([1, null, 3], [2, 99, 6])).toBeCloseTo(1, 10);
  });

  it('pearson returns null with fewer than 3 valid pairs', () => {
    expect(pearson([1, 2], [2, 4])).toBeNull();
  });

  it('rollingCorr emits null until the window is full', () => {
    const r = rollingCorr([1, 2, 3, 4], [2, 4, 6, 8], 3);
    expect(r[0]).toBeNull();
    expect(r[1]).toBeNull();
    expect(r[2]).toBeCloseTo(1, 10);
    expect(r[3]).toBeCloseTo(1, 10);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — `pearson`/`rollingCorr` not exported.

- [ ] **Step 3: Add the implementation**

```ts
// append to web/src/stats.ts

/** Pearson correlation over pairwise-complete observations. Null if < 3 valid pairs. */
export function pearson(xs: Num[], ys: Num[]): number | null {
  const xv: number[] = [];
  const yv: number[] = [];
  const n = Math.min(xs.length, ys.length);
  for (let i = 0; i < n; i++) {
    const a = xs[i];
    const b = ys[i];
    if (a != null && b != null && Number.isFinite(a) && Number.isFinite(b)) {
      xv.push(a);
      yv.push(b);
    }
  }
  const m = xv.length;
  if (m < 3) return null;
  const mx = xv.reduce((s, v) => s + v, 0) / m;
  const my = yv.reduce((s, v) => s + v, 0) / m;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (let i = 0; i < m; i++) {
    const dx = xv[i]! - mx;
    const dy = yv[i]! - my;
    sxy += dx * dy;
    sxx += dx * dx;
    syy += dy * dy;
  }
  const denom = Math.sqrt(sxx * syy);
  return denom === 0 ? null : sxy / denom;
}

/** Trailing rolling Pearson correlation; null until `window` points are available. */
export function rollingCorr(xs: Num[], ys: Num[], window: number): (number | null)[] {
  const out: (number | null)[] = [];
  for (let i = 0; i < xs.length; i++) {
    if (i + 1 < window) {
      out.push(null);
      continue;
    }
    out.push(pearson(xs.slice(i + 1 - window, i + 1), ys.slice(i + 1 - window, i + 1)));
  }
  return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (7 passed total)

- [ ] **Step 5: Commit**

```bash
git add web/src/stats.ts web/test/stats.test.ts
git commit -m "feat(web): pearson + rolling correlation"
```

---

### Task 10: Stats — cross-correlation (lead-lag) + Bartlett band

**Files:**
- Modify: `web/src/stats.ts`
- Modify: `web/test/stats.test.ts`

- [ ] **Step 1: Add the failing test**

```ts
// append to web/test/stats.test.ts
import { crossCorr, bartlettBand } from '../src/stats';

describe('lead-lag', () => {
  it('crossCorr peaks at the lag by which x leads y', () => {
    // y is x shifted forward by 1 (y_t = x_{t-1}); so x leads y by 1 => peak at lag +1.
    const x = [1, 2, 3, 4, 5, 6, 7, 8];
    const y = [0, 1, 2, 3, 4, 5, 6, 7];
    const cc = crossCorr(x, y, 3);
    const peak = cc.reduce((best, c) => ((c.corr ?? -2) > (best.corr ?? -2) ? c : best));
    expect(peak.lag).toBe(1);
    expect(peak.corr).toBeCloseTo(1, 10);
    // symmetric range
    expect(cc[0]!.lag).toBe(-3);
    expect(cc[cc.length - 1]!.lag).toBe(3);
  });

  it('bartlettBand is 2/sqrt(n)', () => {
    expect(bartlettBand(100)).toBeCloseTo(0.2, 10);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — `crossCorr`/`bartlettBand` not exported.

- [ ] **Step 3: Add the implementation**

```ts
// append to web/src/stats.ts

export interface LagCorr {
  lag: number;
  corr: number | null;
}

/**
 * Cross-correlation of x and y over lags [-maxLag, maxLag].
 * corr at lag L = pearson(x_t, y_{t+L}). A positive peak lag means **x leads y**
 * by that many steps. Inputs should already be changes/returns, not levels.
 */
export function crossCorr(xs: Num[], ys: Num[], maxLag: number): LagCorr[] {
  const res: LagCorr[] = [];
  for (let lag = -maxLag; lag <= maxLag; lag++) {
    let a: Num[];
    let b: Num[];
    if (lag >= 0) {
      a = xs.slice(0, xs.length - lag);
      b = ys.slice(lag);
    } else {
      a = xs.slice(-lag);
      b = ys.slice(0, ys.length + lag);
    }
    res.push({ lag, corr: pearson(a, b) });
  }
  return res;
}

/** Approximate ±2/sqrt(n) white-noise significance band for a correlation. */
export function bartlettBand(n: number): number {
  return 2 / Math.sqrt(n);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (9 passed total)

- [ ] **Step 5: Commit**

```bash
git add web/src/stats.ts web/test/stats.test.ts
git commit -m "feat(web): cross-correlation (lead-lag) + bartlett band"
```

---

### Task 11: Typed data loader + window slicing

**Files:**
- Create: `web/src/data.ts`
- Modify: `web/test/stats.test.ts` (add a slicing test) OR create `web/test/data.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// web/test/data.test.ts
import { describe, it, expect } from 'vitest';
import { sliceFrom, type Panel } from '../src/data';

const panel: Panel = {
  dates: ['2019-01-01', '2020-01-01', '2021-01-01', '2022-01-01'],
  series: { eurusd: [1.1, 1.12, 1.18, 1.13], spread10y: [2.5, 1.9, 1.5, 2.8] },
};

describe('sliceFrom', () => {
  it('keeps only rows on/after the start date, across all series', () => {
    const s = sliceFrom(panel, '2021-01-01');
    expect(s.dates).toEqual(['2021-01-01', '2022-01-01']);
    expect(s.series.eurusd).toEqual([1.18, 1.13]);
    expect(s.series.spread10y).toEqual([1.5, 2.8]);
  });

  it('returns the whole panel when start is before all dates', () => {
    expect(sliceFrom(panel, '2000-01-01').dates.length).toBe(4);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot resolve `../src/data`.

- [ ] **Step 3: Write minimal implementation**

```ts
// web/src/data.ts
import type { Num } from './stats';

export interface Panel {
  dates: string[];
  series: Record<string, Num[]>;
}

export interface Dataset {
  meta: { default_start: string };
  daily: Panel;
  monthly: Panel;
}

/** Slice a panel to rows whose date is >= start (ISO yyyy-mm-dd compares lexically). */
export function sliceFrom(panel: Panel, start: string): Panel {
  const from = panel.dates.findIndex((d) => d >= start);
  const i = from === -1 ? panel.dates.length : from;
  const series: Record<string, Num[]> = {};
  for (const [k, v] of Object.entries(panel.series)) {
    series[k] = v.slice(i);
  }
  return { dates: panel.dates.slice(i), series };
}

export async function loadDataset(url = '/data.json'): Promise<Dataset> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`failed to load ${url}: ${res.status}`);
  return (await res.json()) as Dataset;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (data.test.ts: 2 passed)

- [ ] **Step 5: Commit**

```bash
git add web/src/data.ts web/test/data.test.ts
git commit -m "feat(web): typed dataset loader + date-window slicing"
```

---

### Task 12: Chart render helpers + wire the app

**Files:**
- Create: `web/src/charts.ts`
- Modify: `web/src/main.ts`

Rendering is verified manually in the browser (Task 13), not unit-tested.

- [ ] **Step 1: Write `web/src/charts.ts`**

```ts
// web/src/charts.ts
import Plotly from 'plotly.js-dist-min';
import type { Panel } from './data';
import { type Num, diffs, logReturns, rollingCorr, crossCorr, bartlettBand } from './stats';

const LEVEL_TRANSFORM: Record<string, (xs: Num[]) => Num[]> = {
  eurusd: logReturns,
  dxy: logReturns,
  brent: logReturns,
  // yields & spreads: first difference (already in percentage points)
};

/** Apply the change-transform for a series (log-return for prices, diff for yields). */
export function toChanges(name: string, xs: Num[]): Num[] {
  return (LEVEL_TRANSFORM[name] ?? diffs)(xs);
}

/** Overlay: EUR/USD on the left axis, the 10y & 2y spreads on the right axis. */
export function renderOverlay(el: HTMLElement, panel: Panel): void {
  const x = panel.dates;
  const traces = [
    { x, y: panel.series.eurusd, name: 'EUR/USD', yaxis: 'y', type: 'scatter', mode: 'lines' },
    { x, y: panel.series.spread10y, name: 'UST-Bund 10y', yaxis: 'y2', type: 'scatter', mode: 'lines' },
    { x, y: panel.series.spread2y, name: 'UST-Schatz 2y', yaxis: 'y2', type: 'scatter', mode: 'lines' },
  ];
  Plotly.react(el, traces as never, {
    title: 'EUR/USD vs yield spreads (levels)',
    yaxis: { title: 'EUR/USD' },
    yaxis2: { title: 'spread (pp)', overlaying: 'y', side: 'right' },
    margin: { t: 40 },
  } as never);
}

/** Lead-lag: cross-correlation of EUR/USD changes vs 10y-spread changes, with Bartlett band. */
export function renderLeadLag(el: HTMLElement, panel: Panel, maxLag: number): void {
  const fx = toChanges('eurusd', panel.series.eurusd ?? []);
  const sp = toChanges('spread10y', panel.series.spread10y ?? []);
  // x = spread changes, y = fx changes -> positive lag means spread leads FX.
  const cc = crossCorr(sp, fx, maxLag);
  const band = bartlettBand(fx.filter((v) => v != null).length);
  Plotly.react(
    el,
    [{ x: cc.map((c) => c.lag), y: cc.map((c) => c.corr), type: 'bar', name: 'corr' }] as never,
    {
      title: 'Lead-lag: spread vs EUR/USD (changes). Positive lag = spread leads FX',
      xaxis: { title: 'lag (days)' },
      yaxis: { title: 'correlation', range: [-1, 1] },
      shapes: [band, -band].map((yv) => ({
        type: 'line', x0: -maxLag, x1: maxLag, y0: yv, y1: yv,
        line: { dash: 'dot', width: 1, color: '#999' },
      })),
      margin: { t: 40 },
    } as never,
  );
}

/** Rolling correlation of EUR/USD changes vs 10y-spread changes over time. */
export function renderRollingCorr(el: HTMLElement, panel: Panel, window: number): void {
  const fx = toChanges('eurusd', panel.series.eurusd ?? []);
  const sp = toChanges('spread10y', panel.series.spread10y ?? []);
  const rc = rollingCorr(fx, sp, window);
  Plotly.react(
    el,
    [{ x: panel.dates, y: rc, type: 'scatter', mode: 'lines', name: `rolling ${window}d` }] as never,
    {
      title: `Rolling correlation (${window}d): EUR/USD vs 10y spread (changes)`,
      yaxis: { title: 'correlation', range: [-1, 1] },
      margin: { t: 40 },
    } as never,
  );
}
```

- [ ] **Step 2: Replace `web/src/main.ts`**

```ts
// web/src/main.ts
import { loadDataset, sliceFrom, type Dataset } from './data';
import { renderOverlay, renderLeadLag, renderRollingCorr } from './charts';

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el as T;
};

function rerender(data: Dataset): void {
  const start = ($('start') as HTMLInputElement).value || data.meta.default_start;
  const window = Number(($('window') as HTMLInputElement).value);
  const maxLag = Number(($('maxlag') as HTMLInputElement).value);
  const mode = ($('mode') as HTMLSelectElement).value;

  $('windowVal').textContent = String(window);
  $('maxlagVal').textContent = String(maxLag);
  $('warn').textContent =
    mode === 'levels'
      ? 'Levels are non-stationary — correlation on levels may be spurious. Stats use changes regardless.'
      : '';

  const panel = sliceFrom(data.daily, start);
  renderOverlay($('overlay'), panel);
  renderLeadLag($('leadlag'), panel, maxLag);
  renderRollingCorr($('rollcorr'), panel, window);
}

async function boot(): Promise<void> {
  const data = await loadDataset();
  ($('start') as HTMLInputElement).value = data.meta.default_start;
  for (const id of ['mode', 'start', 'window', 'maxlag']) {
    $(id).addEventListener('input', () => rerender(data));
  }
  rerender(data);
}

void boot();
```

- [ ] **Step 3: Type-check the front-end**

Run: `cd web && npx tsc --noEmit`
Expected: no type errors. (If Plotly trace literals error despite the `as never` casts, widen the cast on that call — the runtime shape is correct.)

- [ ] **Step 4: Run the existing unit tests (regression)**

Run: `cd web && npm test`
Expected: PASS (all stats + data tests still green)

- [ ] **Step 5: Commit**

```bash
git add web/src/charts.ts web/src/main.ts
git commit -m "feat(web): overlay, lead-lag, rolling-corr charts + app wiring"
```

---

### Task 13: Manual browser verification

**Files:** none (verification only)

- [ ] **Step 1: Start the dev server**

Run: `make dev` (or `cd web && npm run dev`)
Expected: Vite serves at `http://localhost:5173`.

- [ ] **Step 2: Verify the three views in the browser**

Open `http://localhost:5173` and confirm:
- **Overlay** shows EUR/USD (left axis) and the two spreads (right axis); lines are continuous from the default start (2021) to today.
- **Lead-lag** is a bar chart over lags −60..+60 with a dotted Bartlett band; note the peak lag (the headline "does the spread lead FX?" answer).
- **Rolling correlation** is a line in [−1, 1] that visibly varies over time.
- Dragging **window** / **max lag** sliders updates the charts; changing **Start** reslices; switching **Mode → levels** shows the spurious-trend warning.

- [ ] **Step 3: Build to confirm a clean production bundle**

Run: `cd web && npm run build`
Expected: `web/dist/` produced with no errors.

- [ ] **Step 4: Commit (if vite added any lockfile/config changes)**

```bash
git add -A web
git commit -m "chore(web): verify build" || echo "nothing to commit"
```

---

### Task 14: README + final review

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# EUR/US Bond Scenarios

Quantitative timeseries companion to [`../eur-usd-risk-scenarios`](../eur-usd-risk-scenarios).
Ingests EUR/USD, US & EU 2y/10y yields, the broad-USD index, Brent, and inflation,
then a static front-end plots them and computes correlation / lead-lag in the browser.

See [`CONTEXT.md`](CONTEXT.md) for the domain glossary and decisions, and
[`docs/adr/0001-python-ingest-static-ts-viz.md`](docs/adr/0001-python-ingest-static-ts-viz.md)
for the architecture.

> Scenario / research tooling, **not financial advice.**

## Refresh data (Python)

Requires [uv](https://docs.astral.sh/uv/).

```bash
make data    # fetch FRED + ECB -> data/*.parquet + data/data.json, copy to web/public
```

## Run the app (TypeScript)

```bash
make web-install
make dev      # http://localhost:5173
```

## Views

- **Overlay** — EUR/USD vs the UST−Bund 10y and 2y spreads (levels).
- **Lead-lag** — cross-correlation of EUR/USD changes vs spread changes; a positive peak lag means the spread *leads* FX.
- **Rolling correlation** — how the coupling strengthens/weakens across regimes.

Statistics are always computed on **changes/log-returns** (not levels) to avoid spurious trend correlation.

## Tests

```bash
uv run --directory ingest pytest
cd web && npm test
```
```

- [ ] **Step 2: Run the full test suite (final gate)**

Run: `uv run --directory ingest pytest && cd web && npm test`
Expected: all Python + TS tests pass.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README with refresh + run instructions"
```

---

## Self-Review notes (for the implementer)

- **Spec coverage:** Phase 0 ingest (Tasks 1–6) covers all series in `CONTEXT.md` incl. derived spreads + two-panel monthly model. Phase 1 (Tasks 7–14) covers the three v1 views, levels/changes toggle with warning, date-window default 2021, committed data. Heatmap/scatter intentionally deferred (post-v1).
- **Lead/lag convention** is fixed once in `crossCorr` (x leads y at positive lag) and reused by `renderLeadLag` (x=spread, y=fx) — keep them consistent.
- **Known v1 simplification:** forward-filled holiday gaps produce zero-change days, which mildly *attenuates* (never inflates) correlation — acceptable and conservative. Revisit with per-series real-date masks only if it matters.
- **DXY caveat:** `DTWEXBGS` is the Fed broad-dollar index, a proxy for the ICE DXY (which isn't free on FRED). Documented in `sources.py`.
