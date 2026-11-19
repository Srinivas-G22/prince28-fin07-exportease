# ExportEase

Answers export policy questions for small exporters: Foreign Trade Policy rules, RoDTEP rates, Advance Authorisation and documentation, citing DGFT notifications.

**Status:** Day 1 foundation (FastAPI skeleton, quality gates). Live URL from Day 5.

## Who it's for

Owner of a knitwear export unit in Tiruppur shipping to the EU who wants to claim RoDTEP and use Advance Authorisation.

## The problem

Navigating India's export regulations requires deciphering the Foreign Trade Policy 2023 and its Handbook of Procedures, which are constantly updated across hundreds of scattered notifications and public notices. Exporters must also manually cross-reference complex, multi-page incentive tables structured by HS code to determine correct duty remission rates. As a result, finding active rules and matching them accurately to specific shipment scenarios is error-prone, time-consuming, and risky for small business owners.

## Data sources

Foreign Trade Policy 2023, Handbook of Procedures 2023, DGFT notifications, public notices and trade notices, RoDTEP schedule, ITC(HS) export policy.

- https://www.dgft.gov.in/
- Terms: Public DGFT documents. Cite notification/public notice number and date.

## Hardest problem (my interview story)

Amendments: the FTP is changed by many notifications. Answers must apply the latest amendment, cite its number and date, and look up RoDTEP rates by HS code in a table, not from text.

## Signature feature

HS code dossier: enter an HS code and see export policy, RoDTEP rate and cap, and recent changes.

## Target metric

Correct HS-code lookups for 95%+ of 40 tests; latest-amendment correctness 90%+.

## Run it locally

```bash
uv sync
copy .env.example .env
uv run uvicorn exportease.api.main:create_app --factory --reload
```

`APP_ENV` must be `local`, `ci`, or `production`. The twenty records in
`data/sample_records.json` are a JSON list; unavailable HS-code, rate, or cap
values are `null` rather than inferred.

Run the API checks and quality gate:

```bash
uv run pytest
uv run ruff check .
```
## Run locally in one command

You need Docker Desktop running. From a fresh clone:

```bash
docker compose up --build
```

This starts Postgres (with pgvector), Redis, runs the migrations and loads the sample data once, then starts the API.

- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness (checks the database): http://localhost:8000/ready

Stop with `Ctrl+C`, then `docker compose down`. Add `-v` to also delete the database volume.

## Develop and test

| Task | Mac / Linux | Windows |
|---|---|---|
| Run the API with reload | `make dev` | `uv run poe dev` |
| Unit tests (no network) | `make test` | `uv run poe test` |
| Integration tests (needs `docker compose up`) | `make test-integration` | `uv run poe test-integration` |
| Coverage report | `make cov` | `uv run poe cov` |
| Lint and format check | `make lint` | `uv run poe lint` |
