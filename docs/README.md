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
cp .env.example .env    # Windows: copy .env.example .env
uv run uvicorn exportease.api.main:create_app --factory --reload