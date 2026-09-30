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
