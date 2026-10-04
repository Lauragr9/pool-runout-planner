# Run-Out Planner

A training tool for pool players (8-ball/9-ball). Given the position of the balls left on the table, it works out if there is an order of shots that clears the whole table in one turn (a "run-out"), and if there is not, it  reports the ball where the sequence breaks down.

It is meant as an analysis tool **between games** (like consulting a chess engine after a game), not as an in-game assistant.

## Structure (two domains)

- `domains/layouts/` —-> **Layouts & sessions**: SQLite persistence of ball positions and the player's real attempts.
- `domains/solver/` —-> **Solver engine**: geometry (which shots are blocked by other balls?) plus a backtracking search over both the shot order and, per ball, the shot type (stun/follow/draw). The algorithm itself (`engine.py`, `geometry.py`) never touches the database, but `results_repository.py` saves every computed result to its own `solves` table.

The solver does not enumerate every possible sequence: it returns the best one it finds, or the point where it stops being possible. As mentioned before, for each shot it also picks a shot type (stun, follow, or draw), based on which one actually leaves a solvable position for the rest of the balls, not just a fixed default. "View history" shows the saved result for each layout, not a recomputed one, labelled with the game mode it was solved under. A layout that hasn't been solved yet shows as "Not solved yet." See `ADR.md` for the reasoning.

The game mode (the three tabs at the top) changes which order is actually legal, based on the WPA rules: **Freeform** has no ordering constraint it is just for practicing potential shots and angles, **9-Ball** only allows contacting the lowest-numbered remaining ball next, so the ball with the highest number has to be the last one in the sequence, and **8-Ball** only allows the ball numbered 8 once it is the last one left on the table. Each mode keeps its own independent layout; switching tabs never erases or mixes them.

In **8-Ball**, since one player always has solids (1-7) and the other stripes (9-15), you can optionally say which group is yours. Once chosen, the solver only plans a sequence for your own balls plus the 8 at the end; the opponent's balls stay on the table as fixed obstacles (they can still block a shot) but are never part of the sequence. Leaving it unset keeps the old behavior of planning a full table clear.

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

By default it listens on port `5000` and stores the SQLite database at `data/runout.db` (see Configuration above to change either).

Open `http://localhost:<PORT>/` in the browser, select a game mode (Freeform, 9-Ball, or 8-Ball), and click on the table to place the cue ball. Then, the way of placing the different balls depends on the game mode: in Freeform, simply clicking a spot on the table places a ball (sequentially from lowest to highest number). In 9-Ball and 8-Ball modes, select the specific ball number from the row above the table before clicking the position where you want to place it (9-Ball offers balls 1 through 9; 8-Ball offers the full set of 15 balls: solids 1–7, the 8-ball, and stripes 9–15, represented by a white band over the colored section). In 8-Ball, you can also choose your assigned group (solids or stripes); the opponent's balls will appear dimmed on the table, as their role is to act as obstacles rather than targets to be pocketed. After a successful resolution, you can log whether or not you completed the shot. The "View history" option displays a list of all configurations and the logged attempts associated with them, limited to the 20 most recently created layouts: once you pass that count, older layouts (and any attempts logged against them) stop appearing.

## Tests & coverage

The tests cover the two domains' actual logic (solver geometry/search, and the layouts repository's read/write behavior), not the Flask routes themselves. Repository tests point SQLite at a temporary file per test (see `tests/test_layouts_repository.py`), so they never touch the real `data/runout.db`.

```bash
pip install -r requirements.txt
python -m pytest --cov=domains --cov-report=term-missing
```

Current result: **49 tests, 99% coverage across `domains/layouts` and `domains/solver`**.

## AI disclosure statement

See `AI_USAGE.md` for the detailed, per-interaction log. In short: I used Claude (Anthropic) as an implementation partner, not as the one making the decisions. I made the architectural and scope calls myself, recorded in `ADR.md`, and leaned on the AI to turn those decisions into working code, look up things I didn't want to assume (like the official WPA shot-order rules), and run the empirical checks I asked for, like solvability rates and search performance, instead of just trusting a number. My prompts ranged from those design decisions, to bug reports after testing the app myself in the browser (the rest position landing outside the table, two game modes sharing one board, a cue-rest marker walking straight through an obstacle ball), to asking it to prove a claim empirically rather than assume it. Whatever it produced, I reviewed before keeping: running the test suite, clicking through the app myself, checking numbers by hand or with throwaway scripts. Often I'd come up with my own way of doing something instead of taking the first one offered (like drafting my own version of the rest-position function before asking for a review) and sometimes it would lay out a couple of options where neither quite fit what I had in mind, so I'd push back and suggest a different one.
