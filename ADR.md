# Architecture Decision Record

## [1]. Backend framework: Flask
Date: 2026-09-26
Status: Decided
Context: Necesito servir tanto una API JSON (crear layouts, resolver) como una única página HTML con canvas, todo desde el mismo proceso, en un contenedor único.
Decision: Uso Flask con `sqlite3` de la librería estándar (sin ORM) y Jinja para servir la única página HTML.
Alternatives considered: Django, que trae ORM, panel de admin y un sistema de apps pensado para proyectos con varios modelos y vistas complejas — mucho más de lo que necesito para dos dominios pequeños y una sola página; FastAPI, con soporte async que no aporta nada aquí porque la app la usa una sola persona a la vez y no hay I/O concurrente que aprovechar.
Consequences: Menos boilerplate y menos dependencias que Django, pero tengo que escribir a mano las queries SQL (asumible con dos tablas relacionadas) y no tengo validación automática de payloads como la que traería FastAPI con Pydantic.
