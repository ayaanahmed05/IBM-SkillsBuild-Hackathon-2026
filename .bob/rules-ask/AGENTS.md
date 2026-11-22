# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-Obvious Documentation Context

- **`frontend/src/main.jsx` is the entire frontend** — one file with all components, state, WebSocket logic, and API calls inlined. There are no separate component files, hooks files, or utility modules.
- **`backend/app/engine.py` is the canonical reference for all decision logic** — the README, proof center, and evaluation lab all describe the same algorithm implemented there. If docs and code differ, code is authoritative.
- **IBM runtime claims must follow evidence** — the Proof Center only shows a verified IBM execution after a successful watsonx call has produced a trace. Without credentials or a successful call, the deterministic fallback remains clearly labeled.
- **`backend/src/`** exists (sibling to `backend/app/`) but is currently empty/unused — all application code is under `backend/app/`.
- **The `.env` file belongs in `backend/`**, not the repo root — `pydantic-settings` reads it from the working directory, which is `backend/` when the server is started per README instructions.
- **`bob_sessions/`** at repo root is a Bob AI session evidence directory, not application code. Preserve evidence files.
- **Scenario names map to fixed game states** — `critical`, `timeout`, `resumed`, and `steady`.
