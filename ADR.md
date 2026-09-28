# Architecture Decision Record

## [1]. Backend framework: Flask
Date: 2026-09-26
Status: Decided
Context: I need to serve both a JSON API (create layouts, solve) and a single HTML page with a canvas, all from the same process, in a single container.
Decision: I use Flask with the standard library's `sqlite3` (no ORM) and Jinja to serve the single HTML page.
Alternatives considered: Django, which brings an ORM, an admin panel, and an app system built for projects with many models and complex views. But it's far more than I need for two small domains and a single page; FastAPI, whose async support buys nothing here since the app is used by one person at a time and there is no concurrent I/O to take advantage of.
Consequences: Less boilerplate and fewer dependencies than Django, but I have to write SQL queries by hand (manageable with two related tables) and I don't get automatic payload validation the way FastAPI with Pydantic would give me.

## [2]. Domain boundary: the solver has no persistence dependency
Date: 2026-09-27
Status: Decided
Context: The assignment requires two domains that could later become separate services, so I need a real seam between them, not just two folders that still reach into each other's internals.
Decision: `domains/solver` only works with plain Python dicts (a cue position, a list of balls) and never imports `db` or `domains/layouts`. `app.py` is the only place that connects the two, by reading a layout from the repository and handing it to `find_runout`.
Alternatives considered: attaching a `solve()` method directly onto the layout model/row so persistence and computation live together --> rejected because it would tie the solver's tests to a database, make swapping storage later harder and blur exactly the seam I need to point to for a future service split.
Consequences: I can unit-test the solver with zero database setup (already reflected in the coverage numbers), and moving it into its own service later would only mean replacing an in-process function call in `app.py` with an HTTP call. Nothing inside `domains/solver` itself would need to change.

## [3]. Schema: balls live in their own table, not a JSON column
Date: 2026-09-28
Status: Decided
Context: A layout has a variable number of balls (1 to `MAX_BALLS`), and I need to query them back in a specific order (`ORDER BY ball_number`) without loading and parsing the whole layout just to look at one ball.
Decision: `layouts` (one row per saved table position) has two child tables: `layout_balls` (one row per ball, `layout_id` foreign key, `ball_number`/`x`/`y`) and `attempts` (one row per logged attempt at that layout, `layout_id` foreign key, `succeeded`/`notes`). Both are a standard one-to-many relationship off `layouts`.
Alternatives considered: storing the ball list as a single JSON-encoded text column on `layouts`. Rejected because SQLite can't enforce or query into that structure at the schema level, `get_layout`'s `ORDER BY ball_number` would become application-side sorting after parsing JSON, and adding a per-ball field later (e.g. "was this ball potted") would mean a JSON shape migration instead of a plain `ALTER TABLE`.
Consequences: `get_layout` needs two queries (one for the layout, one for its balls) instead of one, but each ball is individually queryable and indexable, and the schema stays a plain relational diagram instead of an opaque blob.
