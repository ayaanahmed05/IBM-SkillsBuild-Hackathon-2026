# Repository audit and deliberate design decisions

The current repository contains a React/Vite frontend and a Python FastAPI backend. The original Express source under `backend/src` is retained only as audit/reference material and is not the active runtime.

## Compatibility contract

The original endpoint families and primary response keys remain available. The active API adds structured fields for explainable risk, safe-window math, delivery alternatives and recommended fulfillment mode without removing the established state/recommendation contract.

State continues to expose scenario, need, venue, data mode, trip estimate, score, clock, game state, seeded moment intensity and available window. Recommendation continues to expose action, title, explanation, reason, round-trip estimate, trip estimate and metrics.

## Deliberate corrections and upgrades

- `confidence` remains null because Moment Risk is a heuristic, not a probability.
- Moment Risk is no longer a direct copy of seeded `momentIntensity`; it is derived from score margin, quarter/clock, pause/live state, significant events, resumed-play context and possession.
- Significant play yields STAY for every need; active play while away yields RETURN.
- A GO recommendation requires the **complete** round trip to fit the current window, including service and safety buffer.
- Seat delivery is part of recommendation logic when food is requested and leaving is higher risk.
- Accessible routing removes inaccessible facilities/edges before path selection.
- CrowdFlow is now behaviorally distinct from independent MomentGuard choices because it reserves predicted group demand as assignments are generated.
- The cohort experiment uses separate safety and crowd waves so each claimed effect has a fair, understandable test condition.
- Raw developer controls were moved out of the default fan journey into Judge mode.
- The frontend was redesigned around IBM Carbon-inspired interaction/visual hierarchy while avoiding an IBM trademark/logo claim.

## Safety authority

The deterministic backend remains authoritative. Any future IBM/agent proposal must match current session/version and the deterministic action/destination before it can influence the UI. Orders require explicit user confirmation and remain simulated.
