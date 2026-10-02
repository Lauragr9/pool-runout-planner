# Diagrams

Source diagrams for the report (§8). Kept as Mermaid so they render directly on GitHub and stay versioned alongside the code they describe.

## Architecture overview

Matches [ADR-2](../ADR.md): the algorithm itself (`engine.py` + `geometry.py`) never touches the database and stays unit-testable without one, but the solver domain owns a separate `results_repository.py` that saves and re-reads its own computed results — symmetric with how `domains/layouts` owns its own persistence.

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

## Database schema

Matches [ADR-3](../ADR.md) and the actual schema in [`db.py`](../db.py): `layout_balls`, `attempts` and `solves` are all one-to-many child tables off `layouts`, not a JSON blob.

```mermaid
erDiagram
    LAYOUTS ||--o{ LAYOUT_BALLS : has
    LAYOUTS ||--o{ ATTEMPTS : has
    LAYOUTS ||--o{ SOLVES : has

    LAYOUTS {
        int id PK
        text created_at
        real cue_x
        real cue_y
    }
    LAYOUT_BALLS {
        int id PK
        int layout_id FK
        int ball_number
        real x
        real y
    }
    ATTEMPTS {
        int id PK
        int layout_id FK
        text created_at
        int succeeded
        text notes
    }
    SOLVES {
        int id PK
        int layout_id FK
        text computed_at
        int possible
        int failed_at
        text order_json
        text game_mode
        text my_group
    }
```
