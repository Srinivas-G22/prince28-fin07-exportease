# ExportEase

Answers export policy questions for small exporters: Foreign Trade Policy rules, RoDTEP rates, Advance Authorisation and documentation, citing DGFT notifications.

**Status:** Day 1 foundation (FastAPI skeleton, quality gates). Live URL from Day 5.

## Who it's for

Owner of a knitwear export unit in Tiruppur shipping to the EU who wants to claim RoDTEP and use Advance Authorisation.

## The problem

The Foreign Trade Policy 2023 and Handbook of Procedures are amended by many notifications and public notices, and incentive rates sit in large tables by HS code.

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
cp .env.example .env   # Windows: copy .env.example .env
uv run uvicorn exportease.api.main:create_app --factory --reload
```

Then open http://localhost:8000/docs

## Checks

```bash
uv run pytest
uv run ruff check .
```
