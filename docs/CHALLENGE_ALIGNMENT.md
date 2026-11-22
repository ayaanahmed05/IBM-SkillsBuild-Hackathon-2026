# Challenge alignment and judge score strategy

MomentGuard AI is built for the Fan-Centric Sports & Entertainment challenge. The POC addresses a simple high-friction fan decision: **when can I leave my seat, where should I go, and what should I do if conditions change?**

## Completeness and feasibility

- End-to-end React + FastAPI POC with versioned WebSocket state.
- Deterministic safety authority with validated inputs, event history, trip state and failure guards.
- Explainable Moment Risk derived from score margin, game clock, pause/live state and significant-event context.
- Complete trip calculation includes outbound walk, predicted queue, service, return walk and safety buffer.
- Simulated ordering supports explicit confirmation, pickup/delivery and status progression.
- Production container path uses static Vite build behind Nginx and a single-process backend.

## Creativity and innovation

The differentiator is **not** a sports chatbot, generic food ordering, or a static venue map. MomentGuard connects game context to physical venue decisions in real time:

1. GO, WAIT, STAY or RETURN based on the opportunity cost of leaving.
2. Dynamic rerouting when a facility closes, queue load changes or play resumes early.
3. Seat delivery becomes a safety-aware alternative when leaving is the wrong decision.
4. Moment Recovery immediately changes an active trip into a return-to-seat experience.
5. CrowdFlow adds group-demand awareness so a venue can distribute fans rather than creating a new queue spike.

## Design and usability

- IBM Carbon-inspired visual system with a high-contrast decision hierarchy.
- The main decision is understandable in seconds: GO / WAIT / STAY / RETURN NOW.
- Safe-window countdown is the hero metric when a trip is viable.
- Interactive SVG route makes the recommendation visible rather than textual.
- Accessibility preference removes inaccessible paths/facilities before route selection.
- Judge/demo controls are separated from the fan experience.
- Responsive layout supports desktop and mobile demonstration.

## Effectiveness and efficiency

The seeded experiment returns the underlying records so every POC metric is reproducible. Seed 42 / 30 fans currently demonstrates:

- 19 unsafe departures avoided in the tight safety wave.
- 7.33 simulated high-risk exposure minutes avoided.
- Peak food-concession concentration reduced from 100% to 50% in the longer CrowdFlow wave.

All values are explicitly labelled **SIMULATED POC RESULTS**, not real-world performance claims.

## IBM technology story

The application includes a validated adapter boundary, candidate watsonx Orchestrate coordinator/specialist artifacts and a hosted `calculate_moment_risk` tool candidate. The deterministic safety engine remains authoritative. Before submission, the team must complete and capture:

1. A genuine IBM Bob development task.
2. A genuine watsonx Orchestrate invocation using the provisioned team account.
3. A real execution trace showing coordinator → Game Intelligence → `calculate_moment_risk`.
4. Granite only if an entitled Granite model is actually available in that account.

The UI and repository deliberately do not fabricate IBM execution.
