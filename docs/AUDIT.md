# Repository audit and implementation plan

Audited all original source files: frontend/src/{main.jsx,styles.css}, frontend/{index.html,vite.config.js,package.json}, backend/src/{server.js,decisionEngine.js}, backend/package.json and README.md. No existing tests, persistence, websocket, authentication or IBM integration exist. Frontend is React 18/Vite 6; it does not consume the Express API. Styles are independent of backend implementation and will be preserved.

## Original contract
- GET /api/health → {ok,service,mode}
- GET /api/state → {state,recommendation,updatedAt}
- POST /api/scenario {scenario:critical|timeout|resumed} → snapshot; invalid → 400 {error}
- POST /api/need {need:food|restroom|shop} → snapshot; invalid → 400 {error}
- POST /api/reset → snapshot

State: scenario, need, venue, dataMode, trip {walkMinutes,queueMinutes,distanceMeters}, scoreA/B, clock, gameState, momentIntensity, availableWindowMinutes, optional fanAwayFromSeat.
Recommendation: action, confidence, title, explanation, reason, roundTripMinutes, tripEstimate, metrics. Previous confidence and metrics are fabricated constants.

## Deliberate corrections
Response keys remain available. Confidence becomes null (risk is a heuristic score). Impact metrics are measured from event records, initially zero. Significant play yields STAY for every need. Resumed scenario changes game only, never teleports a seated fan. Timeout seed supports a short restroom trip; food may require WAIT. Frontend steady scenario is now a real backend scenario.

## Sequence and files
1. backend/app models, engine, runtime, store, main + tests: validated compatible API and deterministic authoritative runtime.
2. Runtime events, NetworkX venue graph, accessible facility selection, trips/orders, multi-fan assignment and experiment module.
3. WebSocket snapshots, frontend/src API connection and existing layout integration; proxy and Docker Compose.
4. IBM capability discovery and supported integration artifacts, validated proposals, timeout/staleness guards. Cloud execution requires account access and cannot be claimed from config.
5. Regression/integration tests, reproducible measurements, README and evidence requirements.

Node source remains as a reference until replacement verification. Single process is intentional; multiple Uvicorn workers would violate the runtime ownership model.
