# FanFlow AI: MomentGuard

A functioning offline stadium simulation with an existing React/Vite dashboard and a Python FastAPI backend. Recommendations are computed from current game, fan, venue and route state. All game data, venue facilities and orders are explicitly simulated. No real payments, sports feed, IBM cloud execution or IBM Bob usage is claimed.

## Run

Python 3.11+ and Node 22 recommended. From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.lock
cp .env.example backend/.env
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4000 --workers 1
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Frontend proxies `/api` and `/ws` to port 4000. Use one backend worker: runtime ownership is single process. The original Express source remains in backend/src as an audit reference; do not run it on the same port.

Alternatively run `docker compose up --build` from the root. Ports bind only to loopback. Compose configuration was validated; container startup requires a running Docker daemon and has not been verified in this environment. The volume preserves event history across restarts; a process restart starts a new deterministic session rather than resuming an active trip.

## Three-minute demo

1. Initial critical play: STAY. Choose Restroom, then Timeout: GO with an explicit full trip calculation.
2. Start recommended trip. Select Play resumed: RETURN. Advance time until back at the seat: STAY, never RETURN while seated.
3. Reset. Choose Steady game. Spike the recommended facility queue: inspect destination and route changes. Close a facility and check eligible alternatives. Shop plus Accessible routing yields WAIT (seed shop is inaccessible).
4. Confirm a simulated water order; advance 120 seconds for fulfillment or cancel while preparing. No payment occurs.
5. Run the seeded experiment and inspect measured local trip events at `/api/analytics`. Inspect evaluation traces: offline fallback is labelled honestly; no IBM activity is invented.
6. Reset to restore seed facilities, primary fan, orders and critical game. Historical session events remain available.

## API

Interactive validated OpenAPI: http://localhost:4000/docs. Original five endpoint paths and response keys are retained. Intentional safety changes are described in [audit](docs/AUDIT.md).

| Endpoint | Purpose / request |
|---|---|
| GET /api/health, /api/state | Health; complete state and recommendation |
| POST /api/scenario | `{ "scenario": "critical\|timeout\|resumed\|steady" }` (one value) |
| POST /api/need | `{ "need": "food\|restroom\|shop" }` (one value) |
| POST /api/reset | Restore seed data in a new session |
| POST /api/preferences | `{ "accessible": true, "delivery": false, "speed": 60 }` (metres/min) |
| POST /api/simulation/tick | `{ "seconds": 30 }` |
| POST /api/simulation/auto | `{ "enabled": true }` |
| POST /api/facilities/{id} | Optional queue, open, congestion fields |
| POST /api/routes/{from}/{to} | Optional open and congestion fields |
| POST /api/trips/start | Start primary fan's current GO trip |
| GET /api/catalog | Simulated catalog and CAD prices |
| POST /api/orders | facility, item, quantity, mode pickup/delivery, confirmed=true |
| POST /api/orders/{id}/cancel | Only preparing orders |
| POST /api/fans | Unique id, known seat and matching position, need/mobility preferences |
| POST /api/fans/{id}/trip | Start a simulated fan's eligible trip |
| GET /api/crowdflow | Deterministic proposed demand assignment |
| GET /api/events?session_id=… | Persisted chronological events; defaults to current session |
| GET /api/analytics | Actual runtime event totals |
| GET /api/experiments?seed=42&fans=30 | Repeatable cohort calculation with underlying records |
| GET /api/agents | Explicit integration status and evaluation traces |
| WS /ws/live | Initial snapshot, monotonic versioned events, heartbeat and recovery |

Each WebSocket event has type, timestamp, sessionId, stateVersion, payload. Every state event contains a full snapshot, making reconnect and bounded-buffer recovery straightforward. Heartbeats arrive during inactivity. Send `{"type":"snapshot_request"}` for recovery. Client drops older versions. Server version increases even across reset. A browser reload starts fresh version tracking.

## Architecture and decision rules

`models.py` validates inputs; `engine.py` computes eligible routes and complete travel/queue/service/return/buffer time with NetworkX. `runtime.py` owns all mutable simulation state, `store.py` appends SQLite/SQLAlchemy audit records, `main.py` serializes mutations and broadcasts snapshots. `analytics.py` implements demand assignment and reproducible experiments. `agents.py` provides a validated asynchronous adapter boundary and deterministic fallback. Provider interfaces live in `providers.py`; no external provider is implemented.

Significant play prefers STAY. GO requires an eligible trip within the available pause. Insufficient time yields WAIT. Active play while away yields RETURN. Destinations must exist and be open with eligible routes. Every trip includes service and a safety buffer. Risk is a heuristic score, not a probability; compatibility confidence is null. Legacy fabricated impact counters now initialize to zero; measured totals are separate.

Trips progress through walking, queuing, service, returning and completed. Automatic mode advances one simulated second per wall second; manual ticks allow repeatable demonstrations. A pause expires into resumed play. Manual controls also allow queue/congestion spikes, closures and route invalidation.

## Configuration

Copy `.env.example` to backend/.env for local runs. Settings load from the backend working directory or environment:

| Variable | Default / meaning |
|---|---|
| DATABASE_URL | sqlite:///./momentguard.db; event persistence |
| FRONTEND_ORIGIN | http://localhost:5173; CORS and WebSocket Origin |
| API_TOKEN | Empty for loopback demo; require strong token before protected deployment |
| AUTOMATIC | false; automatic progression |
| RISK_THRESHOLD | 75; significant moment score |
| SAFETY_BUFFER_MINUTES | 0.5; trip safety margin |
| AGENT_TIMEOUT_SECONDS | 12; maximum evaluation latency |
| API_PROXY_TARGET | Frontend server target; default http://127.0.0.1:4000 |

When API_TOKEN is set, REST uses `Authorization: Bearer …`. WebSocket sends `{"token":"…"}` as its first message within five seconds; token never goes in the URL. The demo frontend reads `momentguard-token` from sessionStorage. The health endpoint is public. Do not expose the development server publicly. Production authentication, TLS, user isolation and deployment remain separate work.

## Tests and experiments

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m app.analytics --seed 42 --fans 30
cd ../frontend
npm run build
```

Regression tests cover original API shape and invalid inputs, STAY/GO/WAIT/RETURN, seated resumption, queue spikes, closures, inaccessible facilities, route changes, order confirmation/cancellation, WebSocket ordering and recovery, deterministic reset, multiple fans, stale/unsafe/invalid proposals, simulated cloud timeout/authentication failure and fallback. Cloud failure tests use injected adapters and do not prove IBM access.

## IBM and submission evidence

See [IBM setup/status](ibm/README.md). Candidate hosted Python tool and two agent definition generator are supplied, based on official documentation. They have **not** been imported or executed in IBM. Account entitlements, actual models and supported API authentication must be verified before wiring a cloud transport. No real cloud trace exists yet. A real coordinator → Game Intelligence specialist → calculate_moment_risk invocation is the next integration milestone. Other cloud specialists follow that proof.

## Limits and provenance

All arena topology, team scores, queues, capacity and timing are fictional seeds. No third-party dataset, licensing claim or real venue connection is used. Automatic progression is deliberately simple; no realistic basketball possession/score generator is implemented. Crowd occupancy is represented by queue/congestion factors, not a calibrated pedestrian model. Position is tracked at graph waypoints rather than continuous coordinates. Delivery fulfillment is a simulated timer.

Runtime analytics report actual persisted phase durations, queue time, exposure to high-risk play and route changes. The cohort experiment is a deterministic timing estimate for one simultaneous departure wave, not a full stadium optimization trial. It compares nearest-facility baseline, time-eligible MomentGuard and demand-aware assignment using identical fans/seeds. Deferred trips are excluded; totals must be read with completed trip counts. It does not establish real-world improvements or measure calibrated important moments protected. Agent latency is measured locally; no cloud benchmark exists.

Current session state is authoritative in memory; persisted snapshots enable inspection/replay of recorded state, not crash recovery. History is append-only through the app but not protected against direct database edits. Event storage and snapshot broadcast are suitable for a small proof of concept, not production scale. See [phase status](docs/PHASES.md) for remaining work.
