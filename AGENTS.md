# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- **Backend**: Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy 2 · networkx · uvicorn
- **Frontend**: React 18 · Vite 6 · single file (`frontend/src/main.jsx` + `frontend/src/styles.css`)
- **DB**: SQLite (`backend/momentguard.db`); tests always use `sqlite:///:memory:`

## Commands

```bash
# Backend dev (run from backend/)
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4000 --workers 1

# Run all tests (run from backend/)
python -m pytest -q

# Run a single test by name (run from backend/)
python -m pytest -q tests/test_system.py::test_go_wait_return_and_seated_resumption

# Frontend dev (run from frontend/)
npm ci && npm run dev        # http://localhost:5173

# Docker (run from repo root)
docker compose up --build   # http://localhost:8080
```

## Critical Architecture

- **`backend/app/engine.py` is the safety authority**. All recommendations flow through `recommend()` → `risk_breakdown()` → `options()`. IBM/agent layer in `agents.py` may never override this output — it validates proposals against the deterministic result and rejects mismatches.
- **`Runtime` holds all in-memory state** (game, fans, facilities, graph). Every mutation goes through `rt.lock` (asyncio.Lock) and calls `rt.emit()` which increments `stateVersion` and pushes to WebSocket subscribers.
- **`app.main.create_app(settings=None)` is the app factory** used by both production (`app = create_app()` at module bottom) and tests (always pass `Settings(database_url='sqlite:///:memory:')`).
- **WebSocket `/ws/live`** sends a full `Snapshot` on connect, then emits every `rt.emit()` event. Frontend uses monotonic `stateVersion` to discard stale/out-of-order messages.
- **Scenario presets** are the only way to change game state: `critical | timeout | resumed | steady`. Each sets fixed score/clock/window/paused values via `rt.set_scenario()`.

## Backend Code Style

- **No type annotations on function arguments** in most modules — only Pydantic models carry field types.
- **Compact, no-whitespace style** in `main.py` and `runtime.py` (e.g., `a,b,c=data`). Match existing density in those files; `engine.py` and `proof.py` use normal spacing.
- **All API models extend `StrictModel`** (`extra='forbid'`). `GameState` extends plain `BaseModel` with `extra='allow'` (intentional — carries extra game fields).
- **`confidence` field is always `None`** in `Recommendation` — do not populate it; it is a reserved placeholder.
- **Prices in `priceCents` (integer CAD cents)**, times in fractional minutes (float), distances in metres (float).
- **`dataMode` is always the string `'SIMULATED'`** — never change this; it is a provenance contract.

## Testing

- All tests live in `backend/tests/test_system.py` — there is only one test file.
- Tests that do not need HTTP use `create_app(Settings(database_url='sqlite:///:memory:'))` directly (e.g., `test_agent_guards`).
- The `post()` helper in the test file calls `/api/<path>` and asserts `status_code == 200`.
- `experiment(seed, fans)` is deterministic — `experiment(42) == experiment(42)` is a tested invariant.

## Frontend

- The entire frontend is one monolithic component file: `frontend/src/main.jsx`. No routing library, no state manager, no component files.
- Vite proxies `/api` and `/ws` to `http://127.0.0.1:4000` (or `API_PROXY_TARGET` env var).
- Auth token is stored in `sessionStorage` under key `momentguard-token` and sent as `Authorization: Bearer <token>` header on every fetch and as `{token}` JSON on WebSocket connect.
- `accept()` function in `App` enforces monotonic `stateVersion` — messages with lower or equal versions are silently dropped; session changes retire the old session ID.

## Environment / Config

- Backend reads `.env` from the **`backend/`** directory (not repo root). Copy `.env.example` → `backend/.env`.
- `RISK_THRESHOLD=75` is the cutoff where `STAY`/`RETURN` overrides any `GO`. Lowering it makes the engine more conservative.
- `SAFETY_BUFFER_MINUTES=0.5` is added to every round-trip estimate — it is explicit in every `Calculation` response as `safetyBufferMinutes`.
- `API_TOKEN=` empty string disables auth entirely (all requests allowed).
