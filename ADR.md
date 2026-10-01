# Architecture Decision Record

## [1]. Backend framework: Flask
Date: 2026-09-26
Status: Decided
Context: I need to serve both a JSON API (create layouts, solve) and a single HTML page with a canvas, all from the same process, in a single container.
Decision: I use Flask with the standard library's `sqlite3` (no ORM) and Jinja to serve the single HTML page.
Alternatives considered: Django, which brings an ORM, an admin panel, and an app system built for projects with many models and complex views. But it's far more than I need for two small domains and a single page; FastAPI, whose async support buys nothing here since the app is used by one person at a time and there is no concurrent I/O to take advantage of.
Consequences: Less boilerplate and fewer dependencies than Django, but I have to write SQL queries by hand (manageable with two related tables) and I don't get automatic payload validation the way FastAPI with Pydantic would give me.

## [2]. Domain boundary: the solver's algorithm stays pure, its persistence is its own
Date: 2026-09-30
Status: Decided
Context: The assignment requires each domain to demonstrably read/write through SQLite. I originally kept `domains/solver` entirely free of any database dependency, so the solver's only real claim to using SQLite was indirect (the layout `app.py` reads for it before calling it).
Decision: `engine.py` and `geometry.py` still only ever work with plain Python dicts and never import `db`: they stay unit-testable with zero database setup. A separate `domains/solver/results_repository.py` (mirroring `domains/layouts/repository.py`) now saves every computed result to its own `solves` table, and `GET /api/history` reads those saved results back instead of recomputing them each time.
Alternatives considered: keeping the original zero-dependency design and relying on the solver always running on data that was itself read from SQLite --> rejected because it left the domain's own SQLite usage implicit rather than direct, and a persisted results log also gives a genuine audit trail (what the solver actually said at the time, even if the algorithm's parameters change later).
Consequences: the pure algorithm keeps its fast, database-free test suite, but the solver domain now has its own write path and its own table, symmetric with the layouts domain. It also means `/api/history` shows a layout that hasn't been solved yet as "not solved" instead of always computing something for it.

## [3]. Schema: balls live in their own table, not a JSON column
Date: 2026-09-28
Status: Decided
Context: A layout has a variable number of balls (1 to `MAX_BALLS`), and I need to query them back in a specific order (`ORDER BY ball_number`) without loading and parsing the whole layout just to look at one ball.
Decision: `layouts` (one row per saved table position) has two child tables: `layout_balls` (one row per ball, `layout_id` foreign key, `ball_number`/`x`/`y`) and `attempts` (one row per logged attempt at that layout, `layout_id` foreign key, `succeeded`/`notes`). Both are a standard one-to-many relationship off `layouts`.
Alternatives considered: storing the ball list as a single JSON-encoded text column on `layouts`. Rejected because SQLite can't enforce or query into that structure at the schema level, `get_layout`'s `ORDER BY ball_number` would become application-side sorting after parsing JSON, and adding a per-ball field later (e.g. "was this ball potted") would mean a JSON shape migration instead of a plain `ALTER TABLE`.
Consequences: `get_layout` needs two queries (one for the layout, one for its balls) instead of one, but each ball is individually queryable and indexable, and the schema stays a plain relational diagram instead of an opaque blob.

## [4]. Testing approach: line coverage doesn't prove the backtracking actually runs
Date: 2026-09-30
Status: Decided
Context: §4 asks for tests on the "core business logic," not framework glue, at a 70% bar. `coverage.py` already said 98% before today, but line coverage only proves a line executed at least once — it doesn't prove every branch, like the search's backtracking retry, was ever actually exercised.
Decision: Tests target `domains/solver` (geometry + search) and the two repository modules (`domains/layouts`, `domains/solver/results_repository`), using a temporary SQLite file per test; `app.py`'s routes and the frontend have no automated tests, since §4 excludes routing/glue and they were verified manually instead. On top of the coverage number, I specifically looked for and added a test that forces genuine backtracking: a ball with the easiest individual angle that turns out to lead to a dead end two moves later, so the search has to abandon it and fall back to a harder one.
Alternatives considered: writing Flask-test-client integration tests against the routes --> rejected because they'd mostly re-test glue that already delegates to already-tested functions, and the time was better spent closing a real gap in the solver's own logic instead.
Consequences: 98%+ line coverage, but I'm treating that number for what it is: line coverage, not branch coverage, so I can only claim the specific paths I designed a scenario for are proven correct, not every possible path through the search.

## [5]. What I deliberately didn't build: full shot physics
Date: 2026-10-01
Status: Decided
Context: the cue ball's rest position needed to depend on rotation and translation, not just the instantaneous tangent/dot-product geometry it started with. I added a real friction-based slide distance (translation) and a preserved-spin curve for follow and draw shots (rotation): a collision only transfers linear velocity, so whatever spin the cue ball already had keeps pointing along its own original approach direction afterward, which is what actually bends the path.
Decision: I stopped there. `cue_rest_position` supports one assumed shot speed (the solver doesn't choose a different speed per shot) and three shot types (stun, follow, draw, no side-spin/english). The search does try all three shot types per ball, backtracking to a different one (or a different ball entirely) whenever a choice leaves no valid continuation, so the solver genuinely picks the spin that sets up the rest of the table, not just a fixed default. Cushions remain a hard stop rather than a bounce.
Alternatives considered: a full 3D rigid-body simulation, spin as a three-axis vector, proper slip-to-roll friction integration, collision-induced throw, and cushion restitution. I rejected building that because it is genuinely research-level physics (entire papers exist on exactly this), far beyond what a single-process web app for this assignment needs, and the simplified model already demonstrably changes which run-out orders the solver finds (see the backtracking test in ADR-4), which is the part that actually mattered for the assignment.
Consequences: the rest-position numbers are a defensible, documented approximation, good enough to reason about position play qualitatively, not a certified-accurate simulation. Trying 3 shot types per ball also triples the search's branching factor, which I measured directly: worst-case time for an 8-ball layout reached 2.5 seconds, too slow for a single HTTP request, so I lowered `MAX_BALLS` from 8 to 6, which keeps the worst case under ~17ms.
