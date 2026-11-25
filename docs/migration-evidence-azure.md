# Migration evidence on Azure (§4.6)

`services/layouts/migrations/003_add_layout_source.sql` adds `source NVARCHAR(16) NOT NULL
DEFAULT 'ui'` to the `layouts` table on the real Azure deployment (`lgonzalez-ieu2024-layouts`,
backed by its own Azure SQL serverless database), not just in compose. This is the evidence
that the deployed database held data before the migration ran and kept it afterwards.

## 1. Data before the deploy

`GET /layouts` against the live service, before merging the PR that adds migration 003:

```json
[
  {
    "id": 1,
    "created_at": "2026-11-23T21:07:39.966967+00:00",
    "cue": {"x": 51.970443349753694, "y": 29.97193567961165},
    "balls": [
      {"number": 5, "x": 28.078817733990146, "y": 10.918537621359222},
      {"number": 6, "x": 45.812807881773395, "y": 22.326304611650485},
      {"number": 7, "x": 61.083743842364534, "y": 44.535042475728154},
      {"number": 8, "x": 29.310344827586203, "y": 45.50591626213592},
      {"number": 10, "x": 54.187192118226605, "y": 14.923391990291263},
      {"number": 11, "x": 78.57142857142857, "y": 19.292324029126213},
      {"number": 14, "x": 89.16256157635468, "y": 45.14183859223301}
    ],
    "attempts": []
  }
]
```

Layout `id: 1`, created `2026-11-23`, from the manual end-to-end test done right after the
original Phase 8 deploy, predates migration 003 by two days.

## 2. The deployment run

PR #10 ("Add migration 003: layouts gets a NOT NULL + DEFAULT source column") merged to `main`,
triggering `cd.yml`:

https://github.com/Lauragr9/pool-runout-planner/actions/runs/45672244778 (success)

## 3. The startup log line showing the migration

`az containerapp logs show --name lgonzalez-ieu2024-layouts --resource-group rg-lgonzalez-ieu2024 --type console --tail 50`,
captured right after that deploy:

```
{"TimeStamp": "2026-11-25T18:11:09.998323+00:00", "Log": "applied migration 003_add_layout_source.sql"}
{"TimeStamp": "2026-11-25T18:11:09.998323+00:00", "Log": "* Serving Flask app 'app'"}
```

The migration line is printed by `migrate.run_migrations()` inside `create_app()`, before Flask
starts listening (`* Serving Flask app 'app'` on the very next line): proof the migration ran
as part of this exact container's startup, on the real Azure SQL database, not a local run.

## 4. Data after the deploy

`GET /layouts` against the same live service, right after the deploy finished:

```json
[
  {
    "id": 1,
    "created_at": "2026-11-23T21:07:39.966967+00:00",
    "cue": {"x": 51.970443349753694, "y": 29.97193567961165},
    "balls": [
      {"number": 5, "x": 28.078817733990146, "y": 10.918537621359222},
      {"number": 6, "x": 45.812807881773395, "y": 22.326304611650485},
      {"number": 7, "x": 61.083743842364534, "y": 44.535042475728154},
      {"number": 8, "x": 29.310344827586203, "y": 45.50591626213592},
      {"number": 10, "x": 54.187192118226605, "y": 14.923391990291263},
      {"number": 11, "x": 78.57142857142857, "y": 19.292324029126213},
      {"number": 14, "x": 89.16256157635468, "y": 45.14183859223301}
    ],
    "attempts": []
  }
]
```

Identical: same `id`, same `created_at`, same cue and all 7 balls, confirming the row survived
the migration unchanged. `list_recent_layouts()` doesn't select the new `source` column (it was
never wired into the API, since nothing requires it), so it doesn't appear in this response; its
value for this row is backfilled to `'ui'` by the `ALTER TABLE ... DEFAULT` itself, which
`services/layouts/tests/test_migrations.py` proves directly against the schema (seeds a row
under the pre-003 shape, reruns the migration, asserts the row survives with `source == 'ui'`).
