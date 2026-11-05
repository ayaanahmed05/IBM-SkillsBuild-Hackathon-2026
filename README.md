# FanFlow AI: MomentGuard
A runnable full-stack proof of concept for the IBM SkillsBuild AI Experiential Learning Lab.

## What is included
- **Frontend:** React + Vite dashboard with GO / WAIT / STAY / RETURN recommendations.
- **Backend:** Node.js + Express API.
- **Decision engine:** deterministic rules based on simulated game state, queue time, walking time, and fan need.
- **Scenario controls:** critical moment, timeout, and play resumed.
- **Clearly simulated data:** this is a POC, not a live sports or stadium integration.

## Requirements
- Node.js 18+ (20+ recommended)
- npm

## Run locally
Open two terminals.

### 1. Start the backend
```bash
cd backend
npm install
npm run dev
```
Backend runs at `http://localhost:4000`.

### 2. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (usually `http://localhost:5173`).

## API
- `GET /api/health` — health check
- `GET /api/state` — current simulated game/venue state and recommendation
- `POST /api/scenario` — set scenario (`critical`, `timeout`, `resumed`)
- `POST /api/need` — set fan need (`food`, `restroom`, `shop`)
- `POST /api/reset` — reset the simulation

Example:
```bash
curl -X POST http://localhost:4000/api/scenario \
  -H "Content-Type: application/json" \
  -d '{"scenario":"timeout"}'
```

## How the recommendation works
The backend evaluates the current scenario:
- **STAY:** high-impact game moment is in progress.
- **GO:** game is paused and the estimated round trip fits the available window.
- **RETURN:** play has resumed while the fan is away from their seat.
- **WAIT:** the trip is not a good fit for the current window.

The confidence values and impact metrics are illustrative demo values, not statistically calibrated predictions.

## IBM AI integration next
This starter intentionally keeps the decision-critical rules deterministic and auditable. To add IBM services:
1. Create/configure the IBM watsonx.ai project and credentials.
2. Add credentials to `backend/.env` (never commit secrets).
3. Call watsonx.ai from the backend for a natural-language explanation or contextual summary.
4. Keep hard constraints (return time, queue estimates, current game state) validated by backend code; do not let an LLM invent live facts.
5. If the assignment requires agent orchestration, connect the backend workflow to IBM watsonx Orchestrate and document each agent/tool's inputs and outputs.

Real deployments would need licensed/reliable live game data, venue maps, queue feeds, accessibility preferences, and operational monitoring.
