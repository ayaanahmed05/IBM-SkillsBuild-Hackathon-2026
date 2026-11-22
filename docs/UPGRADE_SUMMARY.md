# MomentGuard AI upgrade summary

## Product and UI

- Rebranded the primary experience around MomentGuard AI.
- Replaced dashboard-first hierarchy with a decision-first GO / WAIT / STAY / RETURN experience.
- Added IBM Carbon-inspired light/dark design language, responsive layout and production-style navigation.
- Added safe-window, trip-required and safety-margin hero metrics.
- Added explainable Moment Risk breakdown.
- Added animated SVG smart-route visualization.
- Added visible accessibility eligibility state.
- Added safety-aware seat-delivery alternative and simulated order flow.
- Added Moment Recovery for early play resumption.
- Added Venue Intelligence / operator value screen.
- Added seeded impact cards and hidden Judge mode controls.
- Removed raw JSON/developer controls from the normal fan journey.

## Backend and logic

- Replaced `risk = momentIntensity` with a derived explainable heuristic.
- Added risk breakdown to API response.
- Added safe-window structured response and recommended fulfillment mode.
- Added delivery alternative into recommendation logic.
- Fixed CrowdFlow experiment design so group-demand behavior is genuinely distinct from independent MomentGuard decisions.
- Added two-wave experiment methodology for safety and crowd distribution.
- Added richer, auditable experiment metrics and scorecard.
- Expanded simulated food catalog for a more realistic demo.
- Preserved existing WebSocket, routing, event history, safety guards and trip progression.
- Added regression tests for the new risk/delivery/CrowdFlow behavior.

## Production hardening

- Added multi-stage production frontend Dockerfile.
- Added Nginx static serving, SPA fallback, WebSocket/API proxy and basic security headers.
- Added container health checks and service dependency health gating.
- Removed remote font import from the CSS so the app does not rely on Google Fonts.

## Verification in this workspace

- Backend: **20 tests passed**.
- Frontend JSX: parsed successfully with the installed TypeScript compiler using `--jsx react`.
- CSS/JSX brace-balance sanity checks passed.
- Seed 42 / 30-fan scorecard: 19 unsafe departures avoided, 7.33 simulated high-risk minutes avoided, peak food-concession concentration 100% → 50%.
- Full Vite production build could not be rerun in this environment because npm registry package downloads were unavailable (`EAI_AGAIN`). The locked package files are preserved for normal `npm ci && npm run build` in a connected environment.
- No genuine IBM Bob or watsonx Orchestrate execution is claimed. Those are still required submission evidence.
