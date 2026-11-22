# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Architectural Constraints

- **Deterministic engine is the safety authority — agents cannot override it.** `agents.py:evaluate()` validates that any agent proposal exactly matches `runtime.recommendation()['action']` and `['destination']`; mismatches set `safetyOverride=True` and are rejected. Any architectural change that lets agent output bypass this check breaks the safety contract.
- **`Runtime` is a singleton with shared mutable state.** There is no per-request state isolation — all concurrent API requests share the same `rt` object protected only by `asyncio.Lock`. This works because uvicorn runs with `--workers 1` (single process). Multi-worker deployment would require external state.
- **WebSocket subscribers are `asyncio.Queue(maxsize=32)`.** When full, the oldest event is dropped (`queue.get_nowait()`) and replaced with the new one — every event carries a full recovery snapshot so no state is permanently lost. This is load-shedding by design.
- **SQLite append-only event log** — `Store` only has `append()` and `events()`. There are no deletes, updates, or migrations. The DB is a replay log; in-memory `Runtime` state is the source of truth.
- **`stateVersion` is a session-scoped monotonic integer**, not a global counter — it resets on `rt.reset()` (new `sessionId`). The frontend tracks both `sessionId` and `stateVersion` together to handle session resets correctly.
- **`experiment()` and `evaluation_suite()` are stateless pure functions** — they construct their own `Runtime` instances internally and do not touch the live `rt`. They are safe to call from any context.
- **Frontend has no build-time environment config** — API base URL is always `/api` (proxied by Vite in dev, by nginx in Docker). The only runtime config the frontend reads is `sessionStorage.getItem('momentguard-token')`.
- **`RETURN` action is only possible when `fan.position != fan.seat`** — the `recommend()` function checks the `away` boolean; a seated fan can never receive `RETURN`.
