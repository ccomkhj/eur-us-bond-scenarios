# Context — eur-us-bond-scenarios

The quantitative timeseries companion to the sibling repo
[`eur-usd-risk-scenarios`](../eur-usd-risk-scenarios), which holds a *qualitative*
causal graph for the "EUR/USD → 1.12" macro hypothesis. This repo plots the real
data behind that narrative and measures how the series actually move together.

## Glossary

### Relationship
What the tool computes and shows *beyond* the raw lines. Resolved as a **two-phase**
scope:

- **Phase 1 — Statistical coupling.** Correlation, rolling correlation, lead-lag
  (does the rate differential move *before* EUR/USD?), and derived series such as
  the US–EU yield spread. The data reveals which drivers actually track FX.
- **Phase 2 — Causal-graph overlay.** Annotate the sibling repo's qualitative causal
  edges (e.g. "ECB cuts → EUR yield support weakens") onto the same real timeseries,
  flagging where the data agrees with or contradicts the narrative.

Phase 1 is self-contained and built first; Phase 2 depends on it and on the sibling
repo's YAML model.

### Core series
The minimum set the analysis is built on:

- **EUR/USD** — the FX rate the whole hypothesis is about (dollars per euro).
- **UST10y** — US Treasury 10-year *market yield* (not the coupon).
- **Bund10y** — German 10-year *market yield* (the EU long-rate proxy).

"Interest rate" is deliberately resolved to **market government-bond yields**, not
central-bank **policy rates** — the daily FX carry signal is the market yield gap.

### Yield spread
Derived series **UST10y − Bund10y**. The candidate lead indicator for EUR/USD: the
Phase-1 lead-lag analysis tests whether the spread moves *before* the FX rate.

### Series set
Beyond the core 3, the full ingest set (mapped to the causal chain):

| Series | Role in the hypothesis | Frequency |
|---|---|---|
| EUR/USD | the FX rate under study | daily |
| UST10y, Bund10y | 10y carry; `10y spread` | daily |
| UST2y, Schatz2y | front-end = policy-path expectation; `2y spread` | daily |
| DXY (broad USD) | separates the USD leg from the EUR leg | daily |
| Brent / EU gas | exogenous war→energy trigger (chain start) | daily |
| EU HICP, US CPI | energy→inflation link | **monthly** |

The **mixed frequency** (daily vs monthly inflation) is an explicit modeling
problem the Phase-1 correlation/lead-lag layer must handle (see ADRs).

### Phase 0 — Ingestion (in scope)
No ingestion code or parquet existed at the start, so this repo *owns* ingestion.
The pipeline is **fetch (FRED + ECB Data Portal) → tidy → parquet**, and the viz
layer reads only the parquet. FRED covers most series; **daily Bund/Schatz yields
come from the ECB Data Portal** (FRED's German yields are monthly). The parquet on
disk is the contract between Phase 0 and the Phase-1 viz/stats layer.

### Architecture — two runtimes, static front-end
- **Python (build-time):** fetch FRED/ECB → tidy → **align** all series onto a common
  index → write canonical **parquet** + an exported **`data.json`** for the front-end.
  Python's job is ingestion + alignment; it does *not* run at app runtime.
- **TypeScript (runtime):** a **static** front-end loads `data.json` and computes the
  interactive stats (rolling correlation, lead-lag) **client-side**. Keeps the viz in
  the family's language and needs no server — deployable as a static site.
- **Seam:** `data.json` (aligned tidy series) is the contract. parquet stays canonical
  for reproducibility; JSON is the front-end's read model.

### Levels vs changes
- **Plotting** always uses **levels** (the eye wants the actual EUR/USD and yield lines).
- **Statistics** (correlation, lead-lag) default to **changes** — daily Δ for yields/bps,
  log-returns for EUR/USD, DXY, Brent — because the level series are non-stationary and
  correlating levels yields *spurious* trend-driven correlation.
- The UI exposes a **levels/changes toggle**; the levels mode is shown with a
  "trending → may be spurious" warning so the contrast is a teaching point, not a trap.

### Two-panel frequency model
- **Daily panel** (`daily.parquet`): EUR/USD, UST10y, Bund10y, UST2y, Schatz2y, DXY,
  Brent — on a common business-day index.
- **Monthly panel** (`monthly.parquet`): all of the above resampled to **month-end**,
  plus EU HICP and US CPI.
- Inflation correlation/lead-lag is computed **only on the monthly panel**; rate/FX
  stats use the daily panel. Avoids the release-day "jump" artifact from forcing
  monthly data onto a daily grid.

### History
Ingest **max available** (EUR/USD since the 1999 euro launch; Brent earlier). The app
**defaults** its view to **~2021→now** (the live hypothesis window) but the stored
history enables a later **regime-comparison** toggle.

### Phase-1 app views
1. **Overlay + spread** — multi-series line chart (series toggles, date brush,
   levels/changes toggle) with the 10y & 2y UST–Bund spreads against EUR/USD.
2. **Lead-lag (CCF)** — cross-correlation of EUR/USD changes vs spread changes across
   lags −60..+60 days, peak lag highlighted ("does the spread *lead* FX?").
3. **Rolling correlation** — rolling-correlation strip (window slider) showing *when*
   coupling was strong/weak across regimes.

Deferred: correlation heatmap + scatter/regression (breadth view, post-v1).

### Data in git
The data artifacts (`daily.parquet`, `monthly.parquet`, `data.json`) are intended to be
**committed** — they're tiny (a few thousand daily rows) and the static front-end loads
the JSON directly with no backend. Refresh is **manual** via the ingest CLI
(`make data`); scheduled auto-refresh is a later option, not v1.

> **Current state (real fetch deferred):** FRED's CSV endpoint was unreachable from the
> build environment, so no *real* data is committed yet. The ingest code is correct and
> source-pinned — run `make data` from a network with FRED access to produce and commit
> the real panels. Until then `web/public/data.json` is **gitignored** and produced
> locally by `make sample-data` (synthetic, for offline front-end dev). See
> [`docs/adr/0002-defer-real-data-fetch.md`](docs/adr/0002-defer-real-data-fetch.md).
