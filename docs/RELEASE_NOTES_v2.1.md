# MomentGuard AI v2.1 — Proof Center release

This release adds the judge-visible evidence layer requested after competitive benchmarking of prior IBM sports-AI winners.

## New

- Proof Center with live decision trace
- “Why this / why not?” alternative explanations
- Accessibility eligibility evidence
- Decision assurance and conservative safe-failure explanation
- Honest IBM execution status with verified/unverified boundary
- 100-scenario executable Evaluation Lab
- Baseline vs MomentGuard vs CrowdFlow evidence table
- Judge Mode tabs separating evidence, evaluation and demo controls
- Windows-safe `uvloop` environment marker

## Verification performed in the release workspace

- Backend: **24 automated tests passed**
- Evaluation Lab: **100/100 deterministic simulated scenarios passed**
- Frontend `main.jsx`: parsed successfully with TypeScript JSX parser
- `compose.yaml`: parsed successfully

The full Vite bundle was not regenerated in this packaging environment because package-registry installation was unavailable. Run `npm ci && npm run build` on the submission machine before deploying.

All game, venue and benchmark data is simulated. IBM execution remains explicitly unverified until the team supplies a genuine runtime trace.
