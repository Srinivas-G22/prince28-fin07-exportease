# Capacity plan: ExportEase

Full corpus target: + all amendments, RoDTEP schedules and ITC(HS) policy (6,000+ pages)

<!-- generated:start -->
## Measured on my start corpus (2026-11-23 09:47 UTC)

| What | Value |
|---|---|
| Files | 30 |
| Size on disk | 16.8 MB |
| Pages (PDF pages + 1 per 3,000 characters of text/HTML) | 913 |
| Characters of text | 1,953,845 |
| Estimated tokens (characters / 4) | 488,461 |
| Tokens per page | 535 |
| PDFs with almost no text (scanned? OCR is Day 7) | 20 |
| Files not measured (zip, xlsx, unreadable) | 0 |

## Estimate for the full corpus (target: 6,000 pages)

| What | How | Value |
|---|---|---|
| Scale factor | target / measured | x 6.6 |
| Tokens | measured tokens x scale | 3.21 M |
| Raw files | measured MB x scale | 111 MB |
| Chunks | tokens / 400 x 1.15 overlap | 9,225 |
| Embedding cost, one time | tokens x 1.15 x $0.15 per 1M | $0.55 = Rs 53 |
| Vector storage | chunks x 768 numbers x 4 bytes | 28 MB |
| Text in Postgres | characters x scale x 1.2 | 15 MB |

Assumptions: 4 characters per token, 400-token chunks, 768-dimension embeddings at $0.15 per 1M tokens, Rs 95 per US dollar.
<!-- generated:end -->

## What I conclude

1. Is embedding cost a problem for this product? (1 line, with the number)
2. Do the vectors and text fit in my free Postgres? (1 line: compare with the storage limit on my database dashboard)
3. Which number above am I least sure about, and how will I measure it better? (1 line)
4. What changes if the corpus grows 10 times? (2 lines)
