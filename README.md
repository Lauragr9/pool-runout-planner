# Run-Out Planner

Herramienta de entrenamiento para jugadores de billar (8-ball/9-ball). Dada la posición de las bolas que quedan sobre la mesa, calcula si existe un orden de tacadas que permita correr la mesa entera ("run-out") sin quedarse sin posición, o indica en qué bola se rompe la secuencia si no lo hay.

Pensada como herramienta de análisis **entre partidas** (como un motor de ajedrez que se consulta después de jugar), no como asistente durante una partida en curso.

## Estructura (dos dominios)

- `domains/layouts/` — **Layouts y sesiones**: persistencia en SQLite de las posiciones de bolas y de los intentos reales del jugador.
- `domains/solver/` — **Motor solver**: geometría (¿qué tiros están bloqueados por otras bolas?) + búsqueda con backtracking sobre el orden de tacadas. No escribe en la base de datos, solo lee un layout y devuelve un resultado.

El solver no enumera todas las jugadas posibles: devuelve la mejor secuencia que encuentra, o el punto donde deja de ser posible. Ver `ADR.md` para el razonamiento.

## Requisitos

- Python 3.10+

## Cómo ejecutarlo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Por defecto escucha en el puerto `5000` y guarda la base de datos SQLite en `data/runout.db`. Configurable con variables de entorno:

- `PORT` — puerto de escucha (por defecto `5000`)
- `DATA_DIR` — carpeta donde se guarda `runout.db` (por defecto `data`)

Abre `http://localhost:<PORT>/` en el navegador, coloca la bola blanca y las bolas objetivo haciendo clic sobre la mesa, y pulsa "Guardar y resolver".

## Tests y cobertura

Los tests cubren la lógica de negocio real (el motor solver: geometría + búsqueda), no las rutas Flask ni el CRUD de persistencia.

```bash
pip install -r requirements.txt
python -m pytest --cov=domains.solver --cov-report=term-missing
```

Resultado actual: **12 tests, 96% de cobertura sobre `domains/solver`**.

## Declaración de uso de IA

Ver `AI_USAGE.md` para el registro detallado. Declaración resumen: reconozco el uso de Claude (Anthropic) para generar la estructura inicial del proyecto, el motor solver (geometría y búsqueda con backtracking) y su suite de tests. Los prompts usados incluyen la definición del caso de uso, la petición explícita de que el motor devuelva una única secuencia recomendada en vez de enumerar todas las jugadas posibles, y la petición de montar la estructura del repo. La salida se usó para el andamiaje inicial del código, revisado y verificado (incluyendo ejecución real de los tests y arranque de la app) antes de aceptarlo.
