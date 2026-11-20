# Engineering notes: ExportEase

## D03 · PostgreSQL

### Migrations (upgrade, downgrade, upgrade)

```text
paste the output of:
uv run alembic downgrade -1
uv run alembic current
uv run alembic upgrade head
uv run alembic history
```
Output:
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade 912568e7f9e7 -> 9adc21106c1c, add gin index on metadata
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
9adc21106c1c
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 9adc21106c1c -> 912568e7f9e7, add gin index on metadata
9adc21106c1c -> 912568e7f9e7 (head), add gin index on metadata
<base> -> 9adc21106c1c, create documents and pages


### The loader is idempotent

```text
run 1: records=20 inserted=15 updated=0 unchanged=5
run 2: records=20 inserted=0 updated=0 unchanged=20
run 3 (after editing one record): records=20 inserted=0 updated=1 unchanged=19
```

### EXPLAIN for ?doc_type=VALUE

```text
paste the output of: uv run python scripts/explain.py doc_type VALUE (number "Notification No. 32/2024-25")
```
-- 1) What the planner chooses on its own:
Seq Scan on documents  (cost=0.00..11.00 rows=1 width=36) (actual time=1.126..1.614 rows=1.00 loops=1)
  Filter: (metadata @> '{"number": "Notification No.32/2024-25"}'::jsonb)
  Rows Removed by Filter: 19
  Buffers: shared read=2 dirtied=2
Planning:
  Buffers: shared hit=143 read=8 dirtied=1
Planning Time: 69.259 ms
Execution Time: 1.708 ms

-- 2) Seq scan switched off, to prove the index can be used:
Bitmap Heap Scan on documents  (cost=12.81..16.82 rows=1 width=36) (actual time=1.787..1.788 rows=1.00 loops=1)
  Recheck Cond: (metadata @> '{"number": "Notification No. 32/2024-25"}'::jsonb)
  Heap Blocks: exact=1
  Buffers: shared hit=2 read=2
  ->  Bitmap Index Scan on ix_documents_metadata_gin (cost=0.00..12.81 rows=1 width=0) (actual time=1.743..1.744 rows=1.00 loops=1)
        Index Cond: (metadata @> '{"number": "Notification No. 32/2024-25"}'::jsonb)
        Index Searches: 1
        Buffers: shared hit=1 read=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.083 ms
Execution Time: 1.835 ms


Why did the planner choose a Seq Scan on my table? (2 lines, your own words)

With only 20 rows, PostgreSQL estimates it's cheaper to check the table directly than to pay for an index lookup.

When would it switch to the GIN index? (1 line)
When the table is larger or the filter selective enough that using the index costs less than checking every row.

## D04 · Docker, Compose and tests

### The image

```text
docker images genericfinder:dev
IMAGE               ID             DISK USAGE   CONTENT SIZE   EXTRA
genericfinder:dev   146caec10c1d        300MB           70MB

docker run --rm genericfinder:dev id
uid=999(app) gid=999(app) groups=999(app)
```

- Size: 300 MB (target: under 400 MB)
- First build: not timed. After changing the Dockerfile entry point: not timed.
- The dependency install step was CACHED because `pyproject.toml` and `uv.lock` had not changed.
- The largest layer was `COPY --from=builder /app/.venv /app/.venv` at 96.2 MB; it contains the installed runtime dependencies.
- Production run with `APP_ENV=production`: `/ready` returned HTTP 200 with `database: true`.

### The stack

```text
docker compose ps -a
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED         STATUS                     PORTS
genericfinder-api-1       genericfinder-api        "sh -c 'exec uvicorn…"   api       3 minutes ago   Up 2 minutes (healthy)     0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
genericfinder-db-1        pgvector/pgvector:pg17   "docker-entrypoint.s…"   db        3 minutes ago   Up 2 minutes (healthy)     0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp
genericfinder-migrate-1   genericfinder-migrate    "sh -c 'alembic upgr…"   migrate   3 minutes ago   Exited (0) 2 minutes ago
genericfinder-redis-1     redis:7-alpine           "docker-entrypoint.s…"   redis     3 minutes ago   Up 3 minutes (healthy)     0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp

docker compose logs migrate (first up)
migrate-1  | records=20 inserted=20 updated=0 unchanged=0

docker compose logs migrate (after down + up)
migrate-1  | records=20 inserted=0 updated=0 unchanged=20
```

With `restart: true` under `api.depends_on.db`, `docker compose restart db` restarted the API too; `/ready` returned HTTP 200 with `database: true`.

### Breaking the database on purpose

```text
db stopped:  /health → HTTP 200 {"status":"ok","app":"exportease","env":"local"}
db stopped:  /ready  → HTTP 503 {"status":"not_ready","checks":{"database":false}}
db started:  /ready  → HTTP 200 {"status":"ready","checks":{"database":true}}
```

When the database is down, the load balancer should stop sending requests because the app isn't ready to serve them.
It shouldn't restart the app: the process is healthy, and restarting it won't bring the database back.

### Tests and coverage

```text
uv run poe test              → 17 passed in 0.38s
uv run poe test-integration  → 7 passed in 4.03s
coverage TOTAL, unit only    → TOTAL 286 62 34 2 74%
coverage TOTAL, with integration tests → TOTAL 286 44 34 2 81%
uv run pytest --cov --cov-report=html → 17 passed, 7 skipped; HTML report 74%
```

The new `check_db` failure test covers the exception branch and its `return False` line.

`src/exportease/store.py` is unused by the current database-backed API; its zero coverage is not a runtime gap unless that legacy store is still meant to be supported.
`src/exportease/__init__.py:2` is an unused placeholder `main()`; it matters only if a CLI entry point is added.

## D05 · CI/CD and going live

- Live URL: https://exportease-vu6o.onrender.com
- CI run for pull request 1: [Actions run list](https://github.com/Srinivas-G22/prince28-fin07-exportease/actions) — paste the successful run URL from the PR Checks tab.
- First deploy that ran by itself: paste the CD run URL from Actions.
- Merge commit for PR #7 recorded at 15:34 IST on 2026-11-20; exact click time, smoke-test completion time, and lead time: not captured yet.

### Smoke test output from that CD run

```text
[Paste the last 4 lines of the "Smoke test the live URL" step from the CD run.]
```

### Rollback drill

- Rolled back to SHA `a159742aaa166d8e07c41a508b48c010cd76447f`: start time, smoke-test time, and duration not captured yet.
- Rolled forward to SHA `14a370903e72c2c2b0699b94314d3a9782b445b9`: duration not captured yet.
- The manual rollback workflow skips migrations, so the database remains at its current schema. The migration files are unchanged between these SHAs, so the newer schema is compatible with the older application image for this drill.

### Where my secrets live

- Neon string: GitHub Secret `DATABASE_URL` + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret `RENDER_DEPLOY_HOOK` only.

### Monitoring

- UptimeRobot checks `/health` every 5 minutes; alerts go to my email.
- An always-on Render instance would avoid the free service's cold start after 15 minutes without traffic. [Render free instance details](https://render.com/docs/free)

### Human gate (continuous delivery)

A required reviewer is worth the delay for production changes that could affect customers, data, or compliance; the approval gives someone a chance to review risk and timing.
For routine low-risk changes with strong automated checks and a quick rollback, the approval wait can cost more than it reduces risk.

### Change lead time

Record merge and smoke-test completion times in IST for three CD runs. Lead time is the interval between them.

| CD run | Merge time (IST) | “Smoke test passed” time (IST) | Lead time |
| --- | --- | --- | --- |
| 1 | pending | pending | pending |
| 2 | pending | pending | pending |
| 3 | pending | pending | pending |
| **Average** |  |  | **pending** |

Slowest step: pending until the three CD run logs are compared.
