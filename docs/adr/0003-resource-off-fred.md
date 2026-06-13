# Source every series off FRED, from reachable keyless providers

**Status:** accepted (supersedes [ADR-0002](0002-defer-real-data-fetch.md))

FRED's endpoints are unreachable from this network (confirmed: `fred.stlouisfed.org` times
out while ECB, NY Fed, US Treasury, Yahoo, and BLS all respond), so `make data` could never
produce real data here. Instead of deferring, we **re-sourced every series to a reachable,
keyless provider**, keeping the series *names* identical so the rest of the pipeline and the
whole front-end are unchanged:

| Series | Provider | Endpoint |
|---|---|---|
| EUR/USD, Bund10y, Schatz2y, ECB deposit rate, EU HICP | **ECB Data Portal** | SDMX csvdata (`EXR`/`YC`/`FM`/`ICP` flows) |
| US 2y & 10y par yields | **US Treasury** | official daily-yield-curve CSV (per year) |
| Fed funds (EFFR) | **NY Fed** | `markets.newyorkfed.org` rates API (JSON) |
| DXY, Brent | **Yahoo Finance** | chart API (JSON) |
| US CPI | **BLS** | public timeseries API v1 (keyless, ≤10y/request) |

## Considered options

- **Wait for FRED access (ADR-0002).** Rejected: FRED is blocked from the user's actual
  machine, not just CI, so this never unblocked.
- **stooq for FX/yields/Brent.** Rejected: stooq now serves a JavaScript proof-of-work
  anti-bot challenge instead of CSV — unusable from a script.

## Consequences

- `make data` produces a **fully real** dataset (EUR/USD from 1999; yields, rates, DXY,
  Brent, CPI/HICP over their available ranges) and the panels are committed.
- More provider-specific parsers to maintain (`parse_nyfed_effr_json`, `parse_treasury_csv`,
  `parse_yahoo_chart_json`, `parse_bls_json`) — each unit-tested against captured payloads.
- Provider-specific fragility: Yahoo may rate-limit; BLS v1 caps at 10 years/request (we pull
  the most recent 10); the Treasury CSV is fetched per calendar year.
- DXY is the **ICE US Dollar Index** (Yahoo `DX-Y.NYB`), replacing FRED's broad-dollar proxy
  `DTWEXBGS` — a slightly different index, but the canonical "DXY" the user expects.
