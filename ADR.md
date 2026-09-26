# Architecture Decision Record

## [1]. Backend framework: Flask
Date: 2026-09-26
Status: Decided
Context: I need to serve both a JSON API (create layouts, solve) and a single HTML page with a canvas, all from the same process, in a single container.
Decision: I use Flask with the standard library's `sqlite3` (no ORM) and Jinja to serve the single HTML page.
Alternatives considered: Django, which brings an ORM, an admin panel, and an app system built for projects with many models and complex views — far more than I need for two small domains and a single page; FastAPI, whose async support buys nothing here since the app is used by one person at a time and there is no concurrent I/O to take advantage of.
Consequences: Less boilerplate and fewer dependencies than Django, but I have to write SQL queries by hand (manageable with two related tables) and I don't get automatic payload validation the way FastAPI with Pydantic would give me.
