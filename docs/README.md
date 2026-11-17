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
```

`APP_ENV` must be `local`, `ci`, or `production`. The starter records in
`data/sample_records.json` are a JSON list; unavailable HS-code, rate, or cap
values are `null` rather than inferred.

The sample notification references are public DGFT records:

- [Notification No. 32/2024-25 (30 September 2024)](https://content.dgft.gov.in/Website/dgftprod/8a5fe49d-609d-47ee-9357-2f27b0900fcf/Notification%2032%20Eng.pdf)
- [Notification No. 39/2024-25 (28 October 2024)](https://content.dgft.gov.in/Website/dgftprod/81b20049-2c78-4520-b479-f31954e04a73/Notification%20No.%2039%20%28English%29.pdf)
- [Notification No. 74/2023 (11 March 2024)](https://content.dgft.gov.in/Website/dgftprod/9e50b696-4851-4bbc-b7ba-d4b17622e62c/Notification%2074%20dated%2011.03.2024-English.pdf)
- [Notification No. 70/2023 (8 March 2024)](https://content.dgft.gov.in/Website/dgftprod/b44a72ff-5ccf-4c0b-ad24-a65f5266c926/Notification%20No.70%20dated%2008.03.2024%20English.pdf)
- [Notification No. 60/2023 (13 February 2024)](https://content.dgft.gov.in/Website/English-Notification%20No.%2060-2023.pdf)

Run the API checks and quality gate:

```bash
uv run pytest
uv run ruff check .
```
