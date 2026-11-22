# Verification executed for the upgraded build

- `cd backend && python -m pytest -q`: **20 passed**.
- New tests cover explainable Moment Risk, safety-aware delivery and differentiated CrowdFlow results.
- Seed 42 / 30-fan experiment executed. Scorecard: 19 unsafe departures avoided, 7.33 simulated high-risk exposure minutes avoided, and peak food-concession concentration reduced from 100% to 50% in the longer demand-balancing wave.
- Every experiment result is labelled simulated and returns the underlying trip records and methodology.
- `tsc --jsx react --allowJs --noEmit --skipLibCheck --noResolve src/main.jsx`: JSX syntax parsed successfully.
- CSS and JSX delimiter sanity checks passed.
- A full Vite build was attempted after extracting the repository. The environment could not download locked npm packages because registry access returned `EAI_AGAIN`; therefore no new production-build claim is made here.
- The Docker path is now a multi-stage Vite → Nginx build with API/WebSocket reverse proxy and security headers; actual container startup was not executed in this workspace.
- No IBM account credentials or callable service connector were available. The repository includes IBM-ready artifacts and honest status surfaces, but **no IBM cloud execution, Granite inference or IBM Bob session is claimed**.
