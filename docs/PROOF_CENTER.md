# MomentGuard Proof Center

The Proof Center is the judge-visible evidence layer for MomentGuard AI. It is designed to answer five questions without asking judges to trust a marketing claim:

1. **What inputs did MomentGuard use?** Live simulated game state, fan need, active preferences and safe-window duration.
2. **How was the decision derived?** The same deterministic Moment Risk and route/queue calculations used by the fan UI are shown directly.
3. **What alternatives were rejected and why?** Every eligible route or seat-delivery option carries a human-readable selection/rejection reason.
4. **Did accessibility materially change the decision?** Facility and route eligibility is shown for the active fan profile.
5. **Was IBM actually executed?** IBM status is explicitly verified or unverified. A local fallback is never relabelled as IBM execution.

## Evaluation Lab

`GET /api/evaluation` recomputes exactly 100 deterministic POC scenarios against the production decision functions:

- 30 high-risk game situations
- 30 safe departure windows
- 20 severe queue disruptions
- 10 accessibility-routing cases
- 10 facility-closure cases

The UI reports actual pass/fail counts from the API. Nothing is hard-coded. The suite is a prototype validation harness, not a real-world stadium performance claim.

## Benchmark panel

The Proof Center also displays the existing seeded 30-fan benchmark for baseline, MomentGuard and MomentGuard + CrowdFlow. It is labelled **SIMULATED POC RESULTS** and shows unsafe departures, high-risk exposure and peak food-concession concentration.

## IBM proof boundary

Until the team runs the supplied IBM artifacts in its provisioned account, the panel states **IBM adapter ready · runtime execution not yet verified**. After a genuine trace is captured, the backend can display a verified provider, latency and execution trace. Do not replace this with a fabricated success state.
