import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { makeState, decide } from "./decisionEngine.js";

dotenv.config();
const app = express();
const port = Number(process.env.PORT || 4000);
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || "http://localhost:5173" }));
app.use(express.json());

let currentScenario = "critical";
let currentNeed = "food";

function snapshot() {
  const state = makeState(currentScenario, currentNeed);
  return { state, recommendation: decide(state), updatedAt: new Date().toISOString() };
}

app.get("/api/health", (_req, res) => res.json({ ok: true, service: "FanFlow MomentGuard API", mode: "simulated-data" }));
app.get("/api/state", (_req, res) => res.json(snapshot()));

app.post("/api/scenario", (req, res) => {
  const { scenario } = req.body ?? {};
  if (!["critical", "timeout", "resumed"].includes(scenario)) {
    return res.status(400).json({ error: "scenario must be critical, timeout, or resumed" });
  }
  currentScenario = scenario;
  res.json(snapshot());
});

app.post("/api/need", (req, res) => {
  const { need } = req.body ?? {};
  if (!["food", "restroom", "shop"].includes(need)) {
    return res.status(400).json({ error: "need must be food, restroom, or shop" });
  }
  currentNeed = need;
  res.json(snapshot());
});

app.post("/api/reset", (_req, res) => {
  currentScenario = "critical";
  currentNeed = "food";
  res.json(snapshot());
});

app.listen(port, () => console.log(`MomentGuard API listening on http://localhost:${port}`));
