# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Architectural Constraints

- **Deterministic engine is the safety authority — AI cannot override it.** The watsonx/Granite integration is explanation-only and must never change GO / WAIT / STAY / RETURN decisions.
- **`Runtime` is a singleton with shared mutable state.** There is no per-request state isolation — all concurrent API requests share the same `rt` object protected by `asyncio.Lock`. This works because uvicorn runs with `--workers 1`.
- **WebSocket subscribers are `asyncio.Queue(maxsize=32)`.** Load-shedding is by design and recovery snapshots prevent permanent state loss.
- **SQLite append-only event log** — `Store` only has `append()` and `events()`. In-memory `Runtime` state is the source of truth.
- **`stateVersion` is a session-scoped monotonic integer**, not a global counter.
- **`experiment()` and `evaluation_suite()` are stateless pure functions** and do not touch live runtime state.
- **Frontend API base URL is `/api`** and WebSocket is `/ws/live`; local Vite and production Nginx proxy these paths.
- **`RETURN` action is only possible when `fan.position != fan.seat`**.
- **watsonx credentials are server-side only.** Never expose `WATSONX_API_KEY` or IBM IAM tokens to the frontend, logs, traces, or git.
