# Verification executed in this workspace

- Python 3.13.13 local virtual environment; dependency freeze is backend/requirements.lock. Docker targets Python 3.11; that container runtime has not been exercised.
- `cd backend && .venv/bin/python -m pytest -q`: 18 passed. One upstream Starlette/httpx deprecation warning; no test failures.
- `cd frontend && npm run build`: passed, Vite 6.4.4; original design stylesheet retained with additional runtime control styles.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed. Docker daemon socket is absent, so no container startup claim.
- Seed 42, 30-fan experiment CLI executed. It exports the underlying trip calculation records and policy metrics. MomentGuard and CrowdFlow produced equal outcomes in this seed: there is no demonstrated incremental CrowdFlow benefit here. Different numbers of completed trips make raw totals insufficient to claim improvements.
- Native Chrome loaded the running dashboard at 127.0.0.1:5173 and displayed backend score 106–105, risk score 96, STAY and SIMULATED · CONNECTED. This exposed and led to a fix for the loopback Origin mismatch.
- Automatic approval review rejected subsequent Google Chrome interaction. Further browser click-through testing was not performed. API/WebSocket tests exercise the trip and state transitions instead.
- No IBM account credentials, ADK environment or callable service connector were available. Injected transport tests verify local failure guards; they are not real IBM service tests. No IBM cloud execution, Granite inference, deployment or Bob session evidence exists from this work.
