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
