# Run-Out Planner

A training tool for pool players (8-ball/9-ball). Given the position of the balls left on the table, it works out if there is an order of shots that clears the whole table in one turn (a "run-out"), and if there is not, it reports the ball where the sequence breaks down.

It is meant as an analysis tool **between games** (like consulting a chess engine after a game), not as an in-game assistant.

**Live URL:** https://lgonzalezieu2024ui.z1.web.core.windows.net

## Architecture

Two independent services, split along the domain boundary from Assignment 1 (see [ADR-2](ADR.md), [ADR-6](ADR.md)):

- `services/layouts/`: owns saved table layouts (cue ball + balls) and the attempts logged against them. Its own Azure SQL database.
- `services/solver/`: computes a run-out order for a layout and stores the result. Its own Azure SQL database. Calls `layouts` over HTTP (`GET /layouts/{id}`) to fetch the geometry before solving; this is the one required server-side cross-seam call ([ADR-6](ADR.md)).
- `ui/`: static HTML/CSS/JS, calling both services directly from the browser. Served by `nginx:alpine` locally (no Dockerfile, not a service container), and by an Azure Storage static website in production.

Full system description: [`system.yaml`](system.yaml) (validated against [`system.schema.json`](system.schema.json)), and `services/<name>/openapi.yaml` per service. Decisions and tradeoffs: [`ADR.md`](ADR.md).

## Running locally (docker compose)

```bash
cp .env.example .env   # fill in SA_PASSWORD, LAYOUTS_DB_PASSWORD, SOLVER_DB_PASSWORD
docker compose up --build
```

This brings up SQL Server, a one-off `db-init` job that creates both databases and their logins (idempotent, safe to run again), both services, and the UI:

- UI: http://localhost:8080
- `layouts`: http://localhost:8100 (container port 8000)
- `solver`: http://localhost:8101 (container port 8001)

Both services run their own versioned migrations on startup (`services/<name>/migrations/*.sql`, tracked in a `schema_migrations` table, each one applied at most once).

## Running a single service

Each service is independent and only needs its own database reachable, not the other service running. The quickest way to get one: `docker compose up sqlserver db-init` (brings up just SQL Server and creates both databases/logins, no app containers), then run the service directly from `services/layouts/` or `services/solver/`:

```bash
cd services/layouts   # or services/solver
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL="mssql://layouts_user:<password>@localhost:1433/layouts" python app.py
```

`solver` additionally needs `LAYOUTS_URL` pointing at a running `layouts` instance (default `http://layouts:8000`, override for local use e.g. `http://localhost:8100`). Every environment variable each service reads, with its default, is listed in [`system.yaml`](system.yaml).

## Tests and coverage

Each service has its own test suite and dependency manifest; both need a reachable SQL Server (the compose stack, or any SQL Server instance with that service's database and login already created):

```bash
cd services/layouts   # or services/solver
pip install -r requirements.txt
python -m pytest --cov=. --cov-report=term-missing
```

CI (`.github/workflows/ci.yml`) runs this same command per service against a throwaway SQL Server container on every push and pull request, gated at 70% coverage per service, alongside linting, a `system.yaml`/OpenAPI validation job, and a Docker build of both images. One integration test crossing the seam for real (`tests/integration/test_cross_seam.py`, against the live compose stack) and manually captured partial-failure evidence (stopping one service, see [`docs/partial-failure-evidence.md`](docs/partial-failure-evidence.md)) cover what per-service unit tests can't.

## Deployment

Both services run on Azure Container Apps (Consumption plan, scale to zero), each with its own Azure SQL Database on the serverless free offer, behind a shared SQL logical server. The UI is an Azure Storage static website. See [ADR-8](ADR.md) for the full reasoning (cost model, cold starts, scale-to-zero consequences).

**Pipeline:** every push and pull request runs CI. Every merge to `main` runs `.github/workflows/cd.yml`: it calls `ci.yml` first and only proceeds if that passes, then builds and pushes both images to GHCR (tagged by commit SHA), signs in to Azure via OIDC (a user-assigned managed identity, no password ever stored), points each Container App at the new image, regenerates `ui/config.js` with the live service URLs, uploads the UI to the storage account's `$web` container, and retries `/health` on both services for several minutes before failing the run. Nothing is deployed manually after the initial setup below.

**Reproducing the initial Azure setup** (one-time, done once per subscription, not run by the pipeline): followed the course's Azure deployment guide, with infrastructure as Bicep instead of inline `az` commands ([ADR-8](ADR.md)).

1. Activated Azure for Students, picked an allowed region supporting the SQL free offer (`az policy assignment list` / `az sql db create`'s error message confirm which), and selected the subscription.
2. Registered the required resource providers (`Microsoft.App`, `Microsoft.OperationalInsights`, `Microsoft.Sql`, `Microsoft.Storage`, `Microsoft.ManagedIdentity`) and created the resource group.
3. Deployed `infra/main.bicep` with `infra/main.bicepparam` (`az deployment group create`), which provisions: the Container Apps environment and both Container Apps (placeholder image to start), the shared SQL server and one free-offer serverless database per service, the UI storage account, and the `<prefix>-github` managed identity with Contributor scoped to just this resource group. All passwords come from local environment variables (`readEnvironmentVariable(...)`), never committed.
4. Enabled the storage account's static website feature and created the per-service SQL logins/users (`db/azure-init-master.sql`, then `db/azure-init-db-user.sql` once per database), both data-plane operations Bicep can't express, done as one-off `az`/`sqlcmd` steps.
5. Built and pushed both images to GHCR once by hand, made the packages public, and pointed each Container App at the real image, replacing the placeholder.
6. Created the OIDC federated credential for the managed identity (trusting `repo:<owner>/<repo>:ref:refs/heads/main`) and set it, plus the per-service database passwords, as GitHub Actions secrets; `PREFIX`/`RESOURCE_GROUP`/`UI_STORAGE` as repository variables. From here on, `cd.yml` does every subsequent deploy.
7. Granted the Reader role on the resource group to the course's graders.

## AI usage

I acknowledge the use of Claude Code (Anthropic, Claude Sonnet 5) throughout this project, to scaffold the initial application, design and review the service split and the Azure infrastructure, write tests, debug deployment issues, and draft documentation. The prompts used include asking it to scaffold a domain and its tests, to re-check infrastructure changes against the literal assignment and deployment guide text before deploying anything, to debug specific failing CI/CD runs, and to draft ADR/README content for my own review and edits. The output of these prompts was used to accept, modify, or reject each change individually, recorded row by row in [`AI_USAGE.md`](AI_USAGE.md), the detailed log.
