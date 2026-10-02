# Run-Out Planner

A training tool for pool players (8-ball/9-ball). Given the position of the balls left on the table, it works out whether there is an order of shots that clears the whole table in one turn (a "run-out"), or reports the ball where the sequence breaks down if there isn't.

Meant as an analysis tool **between games** (like consulting a chess engine after a game), not as an in-game assistant.

## Structure (two domains)

- `domains/layouts/` —-> **Layouts & sessions**: SQLite persistence of ball positions and the player's real attempts.
- `domains/solver/` —-> **Solver engine**: geometry (which shots are blocked by other balls?) plus a backtracking search over the shot order. The algorithm itself (`engine.py`, `geometry.py`) never touches the database, but `results_repository.py` saves every computed result to its own `solves` table.

The solver does not enumerate every possible sequence: it returns the best one it finds, or the point where it stops being possible. For each shot it also picks a shot type (stun, follow, or draw), based on which one actually leaves a solvable position for the rest of the balls, not just a fixed default. "View history" shows the saved result for each layout, not a recomputed one, labelled with the game mode it was solved under. A layout that hasn't been solved yet shows as "Not solved yet." See `ADR.md` for the reasoning.

The game mode (the three tabs at the top) changes which order is actually legal, per the WPA rules: **Freeform** has no ordering constraint, **9-Ball** only allows contacting the lowest-numbered remaining ball next, and **8-Ball** only allows the ball numbered 8 once it's the last one left on the table. Each mode keeps its own independent layout; switching tabs never erases or mixes them.

## Architecture

The whole app is a single Flask process (`app.py`), meaning no background workers, queues, or separate services, matching the single-process/single-container deployment contract.

A browser request arrives as JSON over `fetch`, hits a Flask route, and that route is the only place that talks to both domains: it reads or writes through `domains/layouts/repository.py`, hands plain data to the pure solver algorithm in `domains/solver/engine.py`, and saves the result through `domains/solver/results_repository.py`. Everything persists to one SQLite file (see Configuration below).

See [`docs/diagrams.md`](docs/diagrams.md) for the architecture and database schema diagrams, kept in sync with ADR-2 and ADR-3.

## Configuration

The app is configured entirely through environment variables, so no `.env` file is required, and nothing needs editing in the source to reconfigure it:

- `PORT` —-> port Flask listens on (default `5000`)
- `DATA_DIR` —-> folder where the SQLite file (`runout.db`) is stored (default `data`)

Both have sane defaults, so `python app.py` with no environment variables set works out of the box.

## Requirements

- Python 3.10+

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

By default it listens on port `5000` and stores the SQLite database at `data/runout.db` — see Configuration above to change either.

Open `http://localhost:<PORT>/` in the browser, pick a game mode (Freeform, 9-Ball, or 8-Ball), click on the table to place the cue ball, then click "Save & Solve". In 9-Ball and 8-Ball, pick a ball number from the row above the table before clicking where it sits (9-Ball offers 1-9; 8-Ball offers the full 15-ball set, 1-7 solids, 8, and 9-15 stripes, drawn with a white stripe through the colored band). After a successful solve you can log whether you actually ran out with it; "View history" lists recent layouts and their logged attempts.

## Tests & coverage

The tests cover the two domains' actual logic (solver geometry/search, and the layouts repository's read/write behavior), not the Flask routes themselves. Repository tests point SQLite at a temporary file per test (see `tests/test_layouts_repository.py`), so they never touch the real `data/runout.db`.

```bash
pip install -r requirements.txt
python -m pytest --cov=domains --cov-report=term-missing
```

Current result: **39 tests, 98% coverage across `domains/layouts` and `domains/solver`**.

## AI disclosure statement

See `AI_USAGE.md` for the detailed log. Summary: I acknowledge the use of Claude (Anthropic) throughout this project, from the initial scaffold (the two domains, the Flask app, the solver engine, and its test suite) through later iterations: the SQLite schema and the solver's own results table, the result-display redesign, the cue ball's rest-position physics (translation via friction, rotation via preserved spin for follow/draw, and the solver choosing a shot type per ball), the three game modes and their WPA shot-order rules, and the tests covering all of it. The prompts used include the use case definition, explicit scope decisions (e.g. the solver returning one recommended sequence instead of enumerating every play), direct feedback after testing features live in the browser (e.g. the rest position landing outside the table, or looking too lateral to be realistic), and requests to verify claims empirically (e.g. measuring solvability rates and search performance) rather than taking them on faith. Every accepted output was reviewed and verified before being kept, including running the test suite, exercising the app in the browser, and checking specific computed values by hand or with throwaway scripts.
