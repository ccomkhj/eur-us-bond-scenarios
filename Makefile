.PHONY: data sample-data web-install dev test

# Real data: fetch FRED + ECB -> data/*.parquet + data/data.json, then copy where Vite serves it.
data:
	uv run --directory ingest python -m eur_us_bond_ingest.cli
	mkdir -p web/public
	cp data/data.json web/public/data.json

# Offline synthetic sample for front-end dev / CI (writes web/public/data.json directly).
# NOT real market data — use `make data` for that.
sample-data:
	uv run --directory ingest python -m eur_us_bond_ingest.sample

web-install:
	cd web && npm install

dev:
	cd web && npm run dev

test:
	uv run --directory ingest pytest
	cd web && npm test
