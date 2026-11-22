# MomentGuard AI

**Know when to go. Stay for what matters.**

MomentGuard AI is a fan-centric sports and entertainment POC for IBM SkillsBuild. It combines simulated game context, venue flow, fan preferences, accessibility and explainable decision logic to tell a fan when to **GO, WAIT, STAY or RETURN NOW**. CrowdFlow extends the same concept to venue-level demand balancing.

All game, venue, ordering and experiment data in this repository is simulated. No real sports feed, payment, IBM cloud execution or IBM Bob session is claimed.

## What makes the POC different

- Explainable Moment Risk derived from score margin, game clock, pause/live state and event context.
- Complete safe-window math: walk out + queue + service + return + safety buffer.
- Smart route visualization with rerouting and accessible-path eligibility.
- Seat delivery becomes a recommendation when leaving is the higher-risk choice.
- Moment Recovery changes an active trip to RETURN NOW when play resumes early.
- CrowdFlow predicts group demand and spreads fans across eligible concessions.
- Venue Intelligence provides an operator/buyer story in addition to the fan experience.
- Every experiment metric is reproducible and explicitly labelled simulated.
- Judge Mode includes a Proof Center with live decision evidence, rejected alternatives, accessibility checks and IBM execution status.
- Evaluation Lab executes 100 deterministic scenarios against the same decision engine used by the app.

See `docs/CHALLENGE_ALIGNMENT.md` and `docs/DEMO_SCRIPT.md` before submission.

## Local development

Python 3.11+ and Node 22 recommended.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.lock
cp .env.example backend/.env
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4000 --workers 1
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Windows / VS Code quick start

From the repository root in PowerShell:

```powershell
python -m venv .\backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r .\backend\requirements.lock
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 4000
```

The lock file now marks `uvloop` as non-Windows so it no longer blocks installation on Windows. In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

## Proof Center and Evaluation Lab

Turn on **Judge mode** in the top navigation. The default **Proof Center** displays the same live inputs and recommendation used by the fan experience, including the risk breakdown, safe-window evidence, selected and rejected alternatives, accessibility eligibility, decision assurance and IBM execution status. The **Evaluation Lab** executes 100 deterministic scenarios: 30 high-risk states, 30 safe-window cases, 20 queue disruptions, 10 accessibility cases and 10 facility-closure cases. Results are computed, not hard-coded.

IBM execution remains explicitly **unverified** until a real watsonx/Granite/Orchestrate trace is captured from the team's provisioned account.

## Production-style Docker demo

```bash
docker compose up --build
```

Open `http://localhost:8080`. Nginx serves the static frontend and proxies `/api` and `/ws` to the backend.

## Tests

```bash
cd backend
python -m pytest -q
python -m app.analytics --seed 42 --fans 30
cd ../frontend
npm ci
npm run build
```

Current backend result in the upgrade workspace: **24 passed**. The Judge Evaluation Lab also recomputes **100 deterministic scenarios** at runtime.

## Reproducible simulated POC story

Seed 42 / 30 fans currently yields:

- **19** unsafe departures avoided in the 4.5-minute safety wave.
- **7.33 min** simulated high-risk exposure avoided.
- Peak food-concession concentration **100% → 50%** in the 9-minute CrowdFlow wave.

These are prototype simulation outputs, not real-world performance claims.

## IBM integration status

The repository contains:

- validated asynchronous agent adapter boundary with timeout/staleness/safety guards;
- candidate watsonx Orchestrate definitions for `momentguard_coordinator` and `game_intelligence`;
- candidate hosted `calculate_moment_risk` tool aligned to the new explainable heuristic;
- explicit UI status that does not label unverified execution as IBM.

Before submission, the team should complete one genuine IBM Bob task and one genuine watsonx Orchestrate coordinator → specialist → tool invocation in its provisioned account, then save a redacted execution trace. Use Granite only if the entitled account actually lists an appropriate Granite model. See `ibm/README.md`.

## API highlights

- `GET /api/state` — complete versioned state and recommendation
- `POST /api/scenario` — critical / timeout / resumed / steady
- `POST /api/need` — food / restroom / shop
- `POST /api/preferences` — accessibility, delivery and walking speed
- `POST /api/trips/start` — starts only a current GO recommendation
- `POST /api/facilities/{id}` — queue/open/congestion changes
- `GET /api/crowdflow` — demand-aware fan assignment
- `GET /api/experiments?seed=42&fans=30` — reproducible two-wave simulation
- `GET /api/events` and `/api/analytics` — auditable runtime evidence
- `GET /api/proof` — live judge-facing decision trace, alternatives, accessibility evidence and IBM execution status
- `GET /api/evaluation` — executable 100-scenario POC evaluation suite
- `GET /api/agents` — honest IBM integration status and traces
- `WS /ws/live` — versioned real-time snapshots

## Safety and provenance

The deterministic engine remains authoritative. Agent proposals must match the current session/version and deterministic action/destination before they can be accepted. Orders require explicit confirmation and are simulated. Risk is a heuristic, not a probability. The venue, teams, queues and game events are fictional seeds.
