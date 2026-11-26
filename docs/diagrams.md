# Diagrams

Source diagrams for the report (§8b). Kept as Mermaid so they render directly on GitHub and stay versioned alongside the code they describe.

## Architecture, before (Assignment 1 monolith)

Matches [ADR-2](../ADR.md): the algorithm itself (`engine.py` + `geometry.py`) never touches the database and stays unit-testable without one, but the solver domain owns a separate `results_repository.py` that saves and re-reads its own computed results, symmetric with how `domains/layouts` owns its own persistence.

```mermaid
flowchart TB
    Browser["Browser UI<br/>HTML/CSS/vanilla JS, canvas"]

    subgraph Process["Single process: app.py (Flask)"]
        Routes["Flask routes"]
        Layouts["domains/layouts<br/>repository.py"]
        subgraph SolverDomain["domains/solver"]
            Algorithm["engine.py + geometry.py<br/>(pure, no persistence dependency)"]
            ResultsRepo["results_repository.py"]
        end
    end

    DB[("SQLite<br/>data/runout.db")]

    Browser -- "fetch (JSON)" --> Routes
    Routes -- "create/get layout,<br/>log attempt" --> Layouts
    Routes -- "cue + balls<br/>(plain dicts)" --> Algorithm
    Algorithm -- "shot order or<br/>impossible" --> Routes
    Routes -- "save result /<br/>read latest result" --> ResultsRepo
    Routes -- "JSON response" --> Browser
    Layouts <--> DB
    ResultsRepo <--> DB
```

## Architecture, after (Assignment 2 split)

Matches [ADR-6](../ADR.md): the seam from ADR-2 held, and `solver`'s call to `layouts` is the one required server-side cross-seam flow (§3). Each service is its own process, its own container, its own Azure SQL database; the UI is static files calling both directly from the browser.

```mermaid
flowchart TB
    Browser["Browser<br/>ui/ (static HTML/CSS/JS)"]

    subgraph LayoutsSvc["services/layouts (own container)"]
        LayoutsApp["Flask app.py"]
    end
    subgraph SolverSvc["services/solver (own container)"]
        SolverApp["Flask app.py"]
    end

    LayoutsDB[("Azure SQL<br/>lgonzalez-ieu2024-layouts-db")]
    SolverDB[("Azure SQL<br/>lgonzalez-ieu2024-solver-db")]

    Browser -- "create/get/list layouts,<br/>log attempt" --> LayoutsApp
    Browser -- "solve, get solve<br/>(client-side cross-seam<br/>for the history view)" --> SolverApp
    SolverApp -- "GET /layouts/id<br/>server-side cross-seam,<br/>required by §3 / ADR-6" --> LayoutsApp
    LayoutsApp <--> LayoutsDB
    SolverApp <--> SolverDB
```

## Database schema: layouts service

Matches [ADR-3](../ADR.md) (the child-table shape) and `services/layouts/migrations/001_init.sql` + `003_add_layout_source.sql`. `layout_id` in both child tables is a real foreign key, since both tables live in the same database.

```mermaid
erDiagram
    LAYOUTS ||--o{ LAYOUT_BALLS : has
    LAYOUTS ||--o{ ATTEMPTS : has

    LAYOUTS {
        int id PK
        nvarchar created_at
        float cue_x
        float cue_y
        nvarchar source "003: NOT NULL DEFAULT 'ui'"
    }
    LAYOUT_BALLS {
        int id PK
        int layout_id FK
        int ball_number
        float x
        float y
    }
    ATTEMPTS {
        int id PK
        int layout_id FK
        nvarchar created_at
        bit succeeded
        nvarchar notes
    }
```

## Database schema: solver service

Matches [ADR-6](../ADR.md)/[ADR-7](../ADR.md) and `services/solver/migrations/001_init.sql` + `002_add_solve_duration.sql`. `layout_id` is a plain column here, not a foreign key: `layouts` lives in a different database, so SQL Server has no way to enforce it. Integrity is handled in code instead, `solver` only ever writes a row here after successfully reading that exact layout back from `layouts` over HTTP.

```mermaid
erDiagram
    SOLVES {
        int id PK
        int layout_id "plain column, not FK: see ADR-7"
        nvarchar computed_at
        bit possible
        int failed_at
        nvarchar order_json
        nvarchar game_mode
        nvarchar my_group
        float duration_ms "002: nullable"
    }
```

## Deployment

Matches [ADR-8](../ADR.md). Every merge to `main` runs `cd.yml` automatically; nothing here is deployed by hand after the one-time initial setup (README).

```mermaid
flowchart LR
    Dev["git push / merge to main"] --> CI["GitHub Actions: ci.yml<br/>test, lint, SAST, SCA,<br/>image scan, secret scan"]
    CI -- "only if ci.yml passed" --> CD["GitHub Actions: cd.yml"]
    CD -- "docker push, SHA-tagged" --> GHCR["GHCR<br/>pool-runout-planner-layouts/-solver"]
    CD -- "az containerapp update<br/>(OIDC sign-in, no password)" --> Azure

    subgraph Azure["Azure: rg-lgonzalez-ieu2024 (germanywestcentral)"]
        LayoutsCA["Container App<br/>lgonzalez-ieu2024-layouts"]
        SolverCA["Container App<br/>lgonzalez-ieu2024-solver"]
        SQL["SQL server<br/>lgonzalez-ieu2024-sql<br/>(2 serverless databases)"]
        UI["Storage static website<br/>lgonzalezieu2024ui"]
    end

    GHCR -- "image pull" --> LayoutsCA
    GHCR -- "image pull" --> SolverCA
    CD -- "az storage blob upload-batch" --> UI
    LayoutsCA --> SQL
    SolverCA --> SQL
```
