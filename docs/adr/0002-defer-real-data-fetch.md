# Defer the real FRED/ECB data fetch; ship a synthetic sample for offline dev

**Status:** accepted

The committed-data decision (ADR-0001, CONTEXT.md) assumes `data/*.parquet` and `data.json`
are produced by `make data` and committed. During the initial build, **FRED's CSV endpoint
(`fred.stlouisfed.org/fredgraph.csv`) was unreachable** from the build environment (timeouts;
ECB, stooq, and Yahoo were all reachable, so it is a host-specific block, not a general network
failure). Rather than pivot the source away from FRED (which would drop the inflation series and
deviate from ADR-0001), we **kept the FRED+ECB ingest as-is and deferred the real fetch** to a
network with FRED access, and added `make sample-data` — a synthetic generator that reuses the
real pipeline (`build_daily_panel` / `build_monthly_panel` / `df_to_columnar`) to produce a
schema-identical `web/public/data.json` for offline front-end development.

## Consequences

- No real market data is committed yet; `web/public/data.json` is gitignored and regenerated
  locally. Run `make data` from a FRED-reachable network to produce and commit the real panels.
- Because `sample.py` exercises the same alignment/export code as production ingest, the synthetic
  path is a faithful proxy for the data contract — the front-end was verified end-to-end against it.
- If FRED remains unreachable for the user too, the fallback options (stooq for FX/yields/Brent;
  the reachable `api.stlouisfed.org` with a free key) were identified but not implemented.
