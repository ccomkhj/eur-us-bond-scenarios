# Python ingest + static TypeScript viz, stats computed client-side

**Status:** accepted

Data ingestion and alignment run in **Python** (FRED/ECB → tidy → `daily.parquet` +
`monthly.parquet` + an exported `data.json`) as a build-time step; the visualization is
a **static TypeScript front-end** that loads the committed `data.json` and computes the
interactive statistics (rolling correlation, lead-lag) **in the browser**. We chose this
so the viz stays in the same language as the sibling repo `eur-usd-risk-scenarios` and
needs **no server at runtime** (the app deploys/opens as a static artifact), while still
using Python where it is strongest — fetching, cleaning, and aligning the series.

## Considered options

- **All-Python (Streamlit/Dash).** Best stats ergonomics (statsmodels, significance
  tests) but requires a running Python process to view anything and breaks language
  consistency with the family's TS viz.
- **Live Python API (FastAPI) + TS front-end.** Most rigorous (proper cross-correlation
  with significance bands) but adds a backend process to run and maintain — overkill for
  a local exploration tool.
- **Python precomputes a fixed stats grid → JSON.** No backend, but interactivity is
  capped at the precomputed window/lag grid.

## Consequences

- The front-end is self-contained and trivially deployable; data is committed and
  diffable.
- **Cost:** statistics are hand-rolled in JS rather than backed by statsmodels, so we
  forgo built-in significance testing for now. If rigorous inference (e.g. Bartlett
  bands on the CCF, stationarity tests) becomes a requirement, revisit by moving stats
  back to Python — either precomputed or via a thin local API.
- The **`data.json` schema is the contract** between the two runtimes; parquet stays the
  canonical reproducible store.
