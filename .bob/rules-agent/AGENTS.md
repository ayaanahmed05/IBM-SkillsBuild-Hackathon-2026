# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Coding Rules

- **Never modify `engine.py`'s `recommend()` output shape** — `Recommendation` Pydantic model in `models.py` validates it; shape mismatches will raise at runtime.
- **`rt.emit()` must be called inside `async with rt.lock`** in every mutation endpoint — it increments `stateVersion` and pushes to subscribers atomically. Missing the lock causes duplicate/out-of-order versions (see `test_concurrent_mutations_have_unique_event_versions`).
- **`agents.py:evaluate()` double-locks**: it acquires `rt.lock` once to validate proposal freshness, then again to append the trace. Never hold the lock across the entire `await asyncio.wait_for(invoke(...))` — that would deadlock the ticker.
- **Adding a new endpoint**: use `rt.lock`, call `rt.replan()` if facilities/graph/fan changed, call `trigger()` if an agent re-evaluation is needed, return `rt.snapshot()`.
- **Facility dict keys are plain dicts** (not Pydantic models): `id, node, need, name, queue, capacity, service, accessible, delivery, open, congestion`. Do not add keys without updating `options()` in `engine.py`.
- **Route graph nodes are string IDs** (`seat-101`, `junction`, `north`, `south`, `east`). Edges carry `metres, accessible, open, congestion`. The graph is a `networkx.Graph` — undirected.
- **Tests must run from `backend/`** — imports use `from app.xxx import ...` without package prefix; running from repo root will fail.
- **`Fan.trip` state machine**: `None → walking → queuing → service → returning → completed` (or `blocked`). `force_return()` transitions directly to `returning` from any in-progress state.
- **All Pydantic input models use `StrictModel` (`extra='forbid'`)** — adding unexpected fields in tests or API calls returns 400, not a silent ignore.
