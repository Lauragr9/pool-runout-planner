# Run-Out Planner

A training tool for pool players (8-ball/9-ball). Given the position of the balls left on the table, it works out whether there is an order of shots that clears the whole table in one turn (a "run-out"), or reports the ball where the sequence breaks down if there isn't.

Meant as an analysis tool **between games** (like consulting a chess engine after a game), not as an in-game assistant.

## Structure (two domains)

- `domains/layouts/` —-> **Layouts & sessions**: SQLite persistence of ball positions and the player's real attempts.
- `domains/solver/` —-> **Solver engine**: geometry (which shots are blocked by other balls?) plus a backtracking search over the shot order. The algorithm itself (`engine.py`, `geometry.py`) never touches the database, but `results_repository.py` saves every computed result to its own `solves` table.

The solver does not enumerate every possible sequence: it returns the best one it finds, or the point where it stops being possible. "View history" shows the saved result for each layout, not a recomputed one. A layout that hasn't been solved yet shows as "Not solved yet." See `ADR.md` for the reasoning.

## Requirements

- Python 3.10+

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

By default it listens on port `5000` and stores the SQLite database at `data/runout.db`. Configurable via environment variables:

- `PORT` —-> listening port (default `5000`)
- `DATA_DIR` —-> folder where `runout.db` is stored (default `data`)

Open `http://localhost:<PORT>/` in the browser, click on the table to place the cue ball and the object balls, then click "Save & Solve". After a successful solve you can log whether you actually ran out with it; "View history" lists recent layouts and their logged attempts.

## Tests & coverage

The tests cover the two domains' actual logic (solver geometry/search, and the layouts repository's read/write behavior), not the Flask routes themselves. Repository tests point SQLite at a temporary file per test (see `tests/test_layouts_repository.py`), so they never touch the real `data/runout.db`.

```bash
pip install -r requirements.txt
python -m pytest --cov=domains --cov-report=term-missing
```

Current result: **27 tests, 98% coverage across `domains/layouts` and `domains/solver`**.

## AI disclosure statement

See `AI_USAGE.md` for the detailed log. Summary: I acknowledge the use of Claude (Anthropic) to generate the initial project structure, the solver engine (geometry and backtracking search) and its test suite. The prompts used include the definition of the use case, an explicit request that the solver return a single recommended sequence instead of enumerating every possible play, and the request to scaffold the repository. The output was used as the initial code scaffold, reviewed and verified (including actually running the tests and starting the app) before being accepted.
