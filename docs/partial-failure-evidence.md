# Partial-failure evidence (§3, §8b)

Captured against the real `docker compose up --build` stack (not a stub), by stopping `layouts`
and exercising `solver` while it stayed down.

## Setup

A layout already existed in `layouts` (id `3002`), and had been solved once before, so there was
a stored result in `solver` to compare against.

## 1. `solver`'s own health is unaffected by `layouts` being down

```
$ docker compose stop layouts
 Container pool-runout-planner-layouts-1  Stopped

$ curl -sS -w "\nHTTP %{http_code}\n" http://localhost:8101/health
{"db":"ok","status":"ok","version":"dev"}
HTTP 200
```

Confirms §3's "Health reflects the service's own state, not the other service's": `solver`'s
`/health` only checks `solver`'s own database, so it keeps reporting `ok` while `layouts` is
unreachable.

## 2. The cross-seam call fails in a designed way, not a hang or a stack trace

```
$ time curl -sS -w "\nHTTP %{http_code}\n" -X POST http://localhost:8101/layouts/3002/solve \
    -H "Content-Type: application/json" -d '{"game_mode": "freeform"}'
{"error":"layouts service unavailable"}
HTTP 503

real    0m1.559s
```

`client.py`'s `get_layout` retries twice with backoff (`LAYOUTS_RETRIES=2`, sleeping
`0.5 * (attempt + 1)`s between attempts) before raising `LayoutsUnavailable`; `app.py`'s
`solve_layout` route turns that into a clean `503 {"error": "layouts service unavailable"}`
instead of a 500 or a hung connection. Total time (~1.6s) matches the expected retry/backoff
budget, not the full `LAYOUTS_TIMEOUT_S` per attempt, since a stopped container refuses the
connection immediately rather than timing out.

## 3. The UI degrades the same way client-side, for the history view

`ui/js/table.js`'s history loader (`loadHistorySolution`) wraps its own `fetch` to `solver` in a
try/catch and marks that layout's result `"unavailable"` on any failure; the render step then
shows "Results unavailable (solver service unreachable)." next to that layout instead of hiding
it or breaking the page. (Server-side evidence above is from `solver`'s dependency on `layouts`;
this is the inverse, client-side flow from ADR-6, where the UI calls both services itself and one
failing doesn't take down the other's data.)

## 4. Recovery is clean

```
$ docker compose start layouts
 Container pool-runout-planner-layouts-1  Started

$ curl -sS -w "\nHTTP %{http_code}\n" http://localhost:8100/health
{"db":"ok","status":"ok","version":"dev"}
HTTP 200

$ curl -sS -X POST http://localhost:8101/layouts/3002/solve -H "Content-Type: application/json" -d '{"game_mode": "freeform"}'
{"failed_at":null,"order":[...],"possible":true}
HTTP 200
```

No restart of `solver` was needed; the next call after `layouts` came back succeeded immediately.
