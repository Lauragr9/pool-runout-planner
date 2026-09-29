# Diagrams

Source diagrams for the report (§8). Kept as Mermaid so they render directly on GitHub and stay versioned alongside the code they describe.

## Architecture overview

Matches [ADR-2](../ADR.md): `domains/solver` never touches the database directly. `app.py` is the only place that reads a layout from `domains/layouts` and hands plain data to `domains/solver`.

```mermaid
flowchart TB
    Browser["Browser UI<br/>HTML/CSS/vanilla JS, canvas"]

    subgraph Process["Single process: app.py (Flask)"]
        Routes["Flask routes"]
        Layouts["domains/layouts<br/>repository.py"]
        Solver["domains/solver<br/>engine.py + geometry.py<br/>(no persistence dependency)"]
    end

    DB[("SQLite<br/>data/runout.db")]

    Browser -- "fetch (JSON)" --> Routes
    Routes -- "create/get layout,<br/>log attempt" --> Layouts
    Routes -- "cue + balls<br/>(plain dicts)" --> Solver
    Solver -- "shot order or<br/>impossible" --> Routes
    Routes -- "JSON response" --> Browser
    Layouts <--> DB
```

## Database schema

Matches [ADR-3](../ADR.md) and the actual schema in [`db.py`](../db.py): `layout_balls` and `attempts` are both one-to-many child tables off `layouts`, not a JSON blob.

```mermaid
erDiagram
    LAYOUTS ||--o{ LAYOUT_BALLS : has
    LAYOUTS ||--o{ ATTEMPTS : has

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
```
