# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Documentation Context

- **`frontend/src/main.jsx` is the entire frontend** — one ~687-line file with all components, state, WebSocket logic, and API calls inlined. There are no separate component files, hooks files, or utility modules.
- **`backend/app/engine.py` is the canonical reference for all decision logic** — the README, proof center, and evaluation lab all describe the same algorithm implemented there. If docs and code differ, code is authoritative.
- **IBM integration is explicitly unverified** — `ibmExecution.verified` is always `false` in the current codebase. The `/api/agents` and `/api/proof` endpoints openly state this. Do not describe IBM execution as active.
- **`backend/src/`** exists (sibling to `backend/app/`) but is currently empty/unused — all application code is under `backend/app/`.
- **`backend/node_modules/` and `backend/package.json`** exist but are unrelated to the Python app — they appear to be a stale artifact; the backend is pure Python.
- **The `.env` file belongs in `backend/`**, not the repo root — `pydantic-settings` reads it from the working directory, which is `backend/` when the server is started per README instructions.
- **`bob_sessions/`** at repo root is a Bob AI session log directory, not application code.
- **Scenario names map to fixed game states** — `critical` (Q4, 2-pt margin, live), `timeout` (Q4, 1-pt margin, 5-min window, paused), `resumed` (Q4, 1-pt margin, play just resumed), `steady` (Q3, 8-pt margin, 10-min window, paused/intermission).
