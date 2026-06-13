# EUR/US Bond Scenarios

Quantitative timeseries companion to [`../eur-usd-risk-scenarios`](../eur-usd-risk-scenarios).
Ingests EUR/USD, US & EU 2y/10y yields, the broad-USD index, Brent, and inflation,
then a static front-end plots them and computes correlation / lead-lag in the browser.

See [`CONTEXT.md`](CONTEXT.md) for the domain glossary and decisions, and
[`docs/adr/0001-python-ingest-static-ts-viz.md`](docs/adr/0001-python-ingest-static-ts-viz.md)
for the architecture.

> Scenario / research tooling, **not financial advice.**

## Data

Requires [uv](https://docs.astral.sh/uv/).

```bash
make data         # real: fetch FRED + ECB -> data/*.parquet + data/data.json, copy to web/public
make sample-data  # offline: synthetic data.json for front-end dev (NOT real market data)
```

> Note: FRED's CSV endpoint may be unreachable from some networks/CI. The ingest code is
> source-pinned and correct; run `make data` from a network with FRED access to produce the
> real panels. Use `make sample-data` to develop the front-end offline.

## Run the app

```bash
make web-install
make sample-data   # or `make data` if you have the real data
make dev           # http://localhost:5173
```

## Views

- **Overlay** — EUR/USD vs the UST-Bund 10y and 2y spreads (levels).
- **Lead-lag** — cross-correlation of EUR/USD vs spread; a positive peak lag means the spread *leads* FX.
- **Rolling correlation** — how the coupling strengthens/weakens across regimes.

The levels/changes toggle defaults to **changes** (log-returns / first differences); statistics on
**levels** are shown only for contrast and are often spurious (non-stationary series).

## Tests

```bash
make test   # uv run --directory ingest pytest  +  cd web && npm test
```
