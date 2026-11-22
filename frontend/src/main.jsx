import { StrictMode, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const scenarios = [
  ["critical", "Critical play", "High-value possession"],
  ["timeout", "Timeout", "Safe movement window"],
  ["steady", "Steady game", "Longer movement window"],
  ["resumed", "Play resumed", "Recovery mode"],
];

const needMeta = {
  food: { label: "Food", icon: "●", helper: "Concessions or seat delivery" },
  restroom: { label: "Restroom", icon: "◆", helper: "Fastest eligible route" },
  shop: { label: "Fan shop", icon: "■", helper: "Merchandise and essentials" },
};

const nodeCoordinates = {
  "seat-101": [50, 81],
  "seat-102": [42, 81],
  junction: [50, 62],
  north: [50, 18],
  south: [50, 92],
  east: [86, 54],
};

function fmtMinutes(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const total = Math.max(0, Math.round(Number(value) * 60));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function fmtTimeFromNow(minutes) {
  if (minutes === null || minutes === undefined) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(
    new Date(Date.now() + Number(minutes) * 60_000),
  );
}

function pct(value) {
  return `${Math.round(Number(value || 0))}%`;
}

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
    </div>
  );
}

function RiskBreakdown({ items = [], score = 0 }) {
  return (
    <div className="risk-panel">
      <div className="risk-head">
        <div>
          <span className="kicker">EXPLAINABLE DECISION</span>
          <h3>Moment Risk</h3>
        </div>
        <div className="risk-score"><strong>{score}</strong><span>/100</span></div>
      </div>
      <div className="risk-meter"><span style={{ width: `${score}%` }} /></div>
      <div className="risk-list">
        {items.slice(0, 6).map((item, index) => (
          <div className="risk-row" key={`${item.label}-${index}`}>
            <div><strong>{item.label}</strong><small>{item.detail}</small></div>
            <span className={item.points >= 0 ? "risk-plus" : "risk-minus"}>{item.points > 0 ? "+" : ""}{item.points}</span>
          </div>
        ))}
      </div>
      <p className="fine-print">Heuristic decision score, not a probability.</p>
    </div>
  );
}

function VenueMap({ snapshot, recommendation, setNeed }) {
  const path = recommendation?.calculation?.route?.path || [snapshot?.fan?.position || "seat-101"];
  const routePoints = path.map((node) => nodeCoordinates[node]).filter(Boolean).map(([x, y]) => `${x},${y}`).join(" ");
  const selected = snapshot?.fan?.need || "food";
  const facilityMap = Object.fromEntries((snapshot?.facilities || []).map((facility) => [facility.id, facility]));
  const recommendedFacility = facilityMap[recommendation?.destination];

  return (
    <div className="venue-map-shell">
      <div className="venue-map-toolbar">
        <div>
          <span className="kicker">SMART ROUTE</span>
          <h3>{recommendedFacility?.name || "Northstar Arena"}</h3>
        </div>
        <span className="pill neutral">LEVEL 1 · SIMULATED</span>
      </div>
      <div className="map-canvas">
        <svg viewBox="0 0 100 100" role="img" aria-label="Illustrative venue route map">
          <defs>
            <filter id="routeGlow"><feGaussianBlur stdDeviation="1.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>
          <rect x="26" y="27" width="48" height="46" rx="20" className="map-bowl" />
          <rect x="38" y="38" width="24" height="24" rx="5" className="map-court" />
          <line x1="50" y1="39" x2="50" y2="61" className="court-line" />
          <circle cx="50" cy="50" r="4" className="court-line" />
          <path d="M50 81 L50 62 L50 18 M50 62 L50 92 M50 62 L86 54" className="route-network" />
          {routePoints && <polyline points={routePoints} className="active-route" filter="url(#routeGlow)" />}
          <circle cx="50" cy="81" r="3.2" className="map-user" />
          <circle cx="50" cy="18" r="3.1" className={recommendation?.destination?.includes("north") ? "map-node selected-node" : "map-node"} />
          <circle cx="50" cy="92" r="3.1" className={recommendation?.destination?.includes("south") ? "map-node selected-node" : "map-node"} />
          <circle cx="86" cy="54" r="3.1" className={recommendation?.destination?.includes("east") ? "map-node selected-node" : "map-node"} />
          <text x="50" y="13" textAnchor="middle" className="map-text">NORTH MARKET</text>
          <text x="50" y="99" textAnchor="middle" className="map-text">SOUTH</text>
          <text x="86" y="48" textAnchor="middle" className="map-text">SHOP</text>
          <text x="50" y="87" textAnchor="middle" className="map-you-text">YOU</text>
        </svg>
      </div>
      <div className="need-selector compact-selector">
        {Object.entries(needMeta).map(([key, meta]) => (
          <button key={key} className={selected === key ? "need-button active" : "need-button"} onClick={() => setNeed(key)}>
            <span>{meta.icon}</span>{meta.label}
          </button>
        ))}
      </div>
      {recommendation?.calculation && (
        <div className="route-summary">
          <div><span>Walk out</span><strong>{fmtMinutes(recommendation.calculation.route.minutes)}</strong></div>
          <div><span>Queue</span><strong>{fmtMinutes(recommendation.calculation.queueMinutes)}</strong></div>
          <div><span>Service</span><strong>{fmtMinutes(recommendation.calculation.serviceMinutes)}</strong></div>
          <div><span>Return</span><strong>{fmtMinutes(recommendation.calculation.returnRoute.minutes)}</strong></div>
          <div><span>Buffer</span><strong>{fmtMinutes(recommendation.calculation.safetyBufferMinutes)}</strong></div>
        </div>
      )}
    </div>
  );
}

function ImpactCard({ analytics }) {
  const score = analytics?.scorecard;
  const safetyBase = analytics?.waves?.safety?.baseline?.metrics;
  const safetyMoment = analytics?.waves?.safety?.momentguard?.metrics;
  if (!score) return <div className="loading-card">Preparing reproducible POC metrics…</div>;
  return (
    <div className="impact-wrap">
      <div className="impact-banner">
        <span>SIMULATED POC RESULTS</span>
        <strong>Transparent, seeded and reproducible</strong>
        <p>These results demonstrate prototype behavior only. They are not real-world performance claims.</p>
      </div>
      <div className="impact-grid">
        <article className="impact-card">
          <span className="metric-label">UNSAFE DEPARTURES AVOIDED</span>
          <strong>{score.unsafeDeparturesAvoided}</strong>
          <p>{safetyBase?.safetyViolations || 0} baseline violations → {safetyMoment?.safetyViolations || 0} with MomentGuard.</p>
        </article>
        <article className="impact-card">
          <span className="metric-label">HIGH-RISK EXPOSURE AVOIDED</span>
          <strong>{score.highRiskMinutesAvoided}<em> min</em></strong>
          <p>Calculated from the same 30-fan seeded safety wave.</p>
        </article>
        <article className="impact-card highlight">
          <span className="metric-label">PEAK FOOD CONCENTRATION</span>
          <strong>{score.crowdPeakConcentrationBeforePct}% <b>→</b> {score.crowdPeakConcentrationAfterPct}%</strong>
          <p>CrowdFlow balances predicted concession demand in the longer crowd wave.</p>
        </article>
      </div>
    </div>
  );
}


function ProofCenter({ proof, analytics, onRefresh, onRunGranite, ibmRunning, ibmStatus }) {
  if (!proof) return <div className="loading-card">Building live decision evidence…</div>;
  const final = proof.finalDecision || {};
  const ibm = proof.ibmExecution || {};
  const safety = analytics?.waves?.safety;
  const crowd = analytics?.waves?.crowd;
  function foodPeakPct(metrics) {
    const counts = metrics?.facilityUtilization || {};
    const north = Number(counts["food-north"] || 0);
    const south = Number(counts["food-south"] || 0);
    const total = north + south;
    return total ? Math.round(Math.max(north, south) / total * 100) : 0;
  }
  const benchmarkRows = [
    ["Without MomentGuard", safety?.baseline?.metrics, crowd?.baseline?.metrics],
    ["With MomentGuard", safety?.momentguard?.metrics, crowd?.momentguard?.metrics],
    ["MomentGuard + CrowdFlow", safety?.crowdflow?.metrics, crowd?.crowdflow?.metrics],
  ];

  return (
    <div className="proof-center" id="proof-center">
      <div className="proof-hero">
        <div>
          <span className="kicker">MOMENTGUARD PROOF CENTER</span>
          <h3>See exactly why this decision was made.</h3>
          <p>Live inputs, deterministic calculations, rejected alternatives, accessibility checks, IBM execution status and reproducible benchmarks in one judge-facing evidence layer.</p>
        </div>
        <button className="secondary-button" onClick={onRefresh}>Refresh evidence</button>
      </div>

      <div className="proof-grid">
        <article className="proof-card trace-card">
          <div className="proof-card-head"><span>01</span><div><small>LIVE INPUT</small><h4>Game + fan request</h4></div></div>
          <div className="proof-scoreline"><strong>{proof.game?.score}</strong><span>Q{proof.game?.quarter} · {Math.floor((proof.game?.clockSeconds || 0)/60)}:{String((proof.game?.clockSeconds || 0)%60).padStart(2,"0")}</span></div>
          <div className="evidence-kv"><span>Need</span><strong>{proof.request?.need}</strong></div>
          <div className="evidence-kv"><span>Safe window</span><strong>{fmtMinutes(proof.game?.availableWindowMinutes)}</strong></div>
          <div className="evidence-kv"><span>Accessible profile</span><strong>{proof.request?.accessible ? "ON" : "OFF"}</strong></div>
          <div className="evidence-kv"><span>Seat delivery</span><strong>{proof.request?.seatDelivery ? "ON" : "OFF"}</strong></div>
        </article>

        <article className="proof-card trace-card">
          <div className="proof-card-head"><span>02</span><div><small>GAME INTELLIGENCE</small><h4>Explainable Moment Risk</h4></div></div>
          <div className="proof-risk"><strong>{proof.risk?.score}</strong><span>/100</span></div>
          <div className="mini-risk-list">
            {(proof.risk?.breakdown || []).slice(0, 6).map((item, index) => (
              <div key={`${item.label}-${index}`}><span>{item.label}</span><b>{item.points > 0 ? "+" : ""}{item.points}</b></div>
            ))}
          </div>
          <small className="proof-note">{proof.risk?.scale}</small>
        </article>

        <article className="proof-card final-proof-card">
          <div className="proof-card-head"><span>03</span><div><small>FINAL DECISION</small><h4>{final.action}</h4></div></div>
          <div className={`proof-action action-${String(final.action || "WAIT").toLowerCase()}`}>{final.action}</div>
          <strong className="proof-title">{final.title}</strong>
          <p>{final.reason}</p>
          <div className="assurance-row"><span>DECISION ASSURANCE</span><strong>{final.assurance}</strong></div>
          <small>{final.assuranceReason}</small>
        </article>
      </div>

      <article className="proof-section-card">
        <div className="surface-heading"><div><span className="kicker">WHY THIS · WHY NOT?</span><h3>Options evaluated</h3></div><span className="pill neutral">LIVE ENGINE OUTPUT</span></div>
        <div className="option-evidence-list">
          {(proof.options || []).map((option, index) => (
            <details className={option.selected ? "option-proof selected" : "option-proof"} key={`${option.destination}-${index}`} open={option.selected}>
              <summary>
                <span className={option.selected ? "proof-check selected" : "proof-check"}>{option.selected ? "✓" : "×"}</span>
                <div><strong>{option.name}</strong><small>{option.delivery ? `Seat delivery · ETA ${fmtMinutes(option.roundTripMinutes)}` : `Round trip ${fmtMinutes(option.roundTripMinutes)}`}</small></div>
                <b>{option.decision}</b>
              </summary>
              <p>{option.why}</p>
            </details>
          ))}
        </div>
        {proof.whyNotLeaveNow && <div className="why-not-callout"><span>WHY NOT LEAVE NOW?</span><p>{proof.whyNotLeaveNow}</p></div>}
      </article>

      <div className="proof-two-col">
        <article className="proof-section-card">
          <div className="surface-heading"><div><span className="kicker">ACCESSIBILITY EVIDENCE</span><h3>Preferences change eligibility</h3></div><span className={proof.accessibility?.enabled ? "pill live" : "pill neutral"}>{proof.accessibility?.enabled ? "ACTIVE" : "STANDARD"}</span></div>
          <div className="access-proof-list">
            {(proof.accessibility?.checks || []).map((check) => (
              <div className={check.eligible ? "access-proof eligible" : "access-proof rejected"} key={check.facility}>
                <span>{check.eligible ? "✓" : "×"}</span><div><strong>{check.name}</strong><small>{check.why}</small></div>
              </div>
            ))}
          </div>
        </article>

        <article className="proof-section-card ibm-runtime-card">
          <div className="surface-heading"><div><span className="kicker">IBM AI EXECUTION</span><h3>{ibm.verified ? "Verified runtime trace" : "Integration status"}</h3></div><span className={ibm.verified ? "pill live" : "pill warning"}>{ibm.verified ? "VERIFIED" : "UNVERIFIED"}</span></div>
          <div className="ibm-trace">
            {(ibm.steps || []).map((step, index) => (
              <div className={`ibm-step ${step.status}`} key={`${step.label}-${index}`}><span>{step.status === "verified" || step.status === "local" ? "✓" : "○"}</span><strong>{step.label}</strong><small>{step.status.toUpperCase()}</small></div>
            ))}
          </div>
          {ibm.model && <div className="evidence-kv"><span>Granite model</span><strong>{ibm.model}</strong></div>}
          {ibm.latencyMs !== null && ibm.latencyMs !== undefined && <div className="evidence-kv"><span>Runtime latency</span><strong>{ibm.latencyMs} ms</strong></div>}
          {ibm.verified && ibm.explanation && <div className="granite-explanation"><span>GRANITE EXPLANATION</span><p>{ibm.explanation}</p></div>}
          {!ibm.verified && <p className="truth-callout">{ibm.note}</p>}
          <div className="ibm-action-row">
            <button className="secondary-button" disabled={!ibmStatus?.configured || ibmRunning} onClick={onRunGranite}>
              {ibmRunning ? "Calling IBM Granite…" : ibmStatus?.configured ? "Run IBM Granite explanation" : "Add watsonx credentials to enable"}
            </button>
            <small>{ibmStatus?.configured ? "Real IBM Cloud call · explanation-only" : "backend/.env → WATSONX_API_KEY, PROJECT_ID, MODEL_ID"}</small>
          </div>
        </article>
      </div>

      <article className="proof-section-card benchmark-card">
        <div className="surface-heading"><div><span className="kicker">SIMULATED POC RESULTS</span><h3>Baseline vs MomentGuard vs CrowdFlow</h3></div><span className="pill neutral">SEED 42 · 30 FANS</span></div>
        <p className="proof-disclaimer">Reproducible prototype simulation only. These are not real-world stadium performance claims.</p>
        <div className="benchmark-table" role="table" aria-label="MomentGuard benchmark comparison">
          <div className="benchmark-row header"><span>Policy</span><span>Unsafe departures</span><span>High-risk exposure</span><span>Peak food load</span></div>
          {benchmarkRows.map(([label, safetyMetrics, crowdMetrics]) => (
            <div className="benchmark-row" key={label}><strong>{label}</strong><span>{safetyMetrics?.safetyViolations ?? "—"}</span><span>{safetyMetrics ? `${safetyMetrics.importantMomentExposureMinutes} min` : "—"}</span><span>{crowdMetrics ? `${foodPeakPct(crowdMetrics)}%` : "—"}</span></div>
          ))}
        </div>
      </article>
    </div>
  );
}

function EvaluationLab({ evaluation, onRun }) {
  if (!evaluation) return <div className="loading-card">Preparing the 100-scenario evaluation suite…</div>;
  return (
    <div className="evaluation-lab">
      <div className="evaluation-hero">
        <div><span className="kicker">MOMENTGUARD EVALUATION LAB</span><h3>{evaluation.passed} / {evaluation.total} scenarios passed</h3><p>Every score below is generated by executable scenarios against the same decision engine used by the app.</p></div>
        <div className="evaluation-score"><strong>{evaluation.passRatePct}%</strong><span>PASS RATE</span></div>
        <button className="secondary-button" onClick={onRun}>Run suite again</button>
      </div>
      <div className="evaluation-grid">
        {(evaluation.categories || []).map((category) => (
          <article className="evaluation-card" key={category.id}>
            <span>{category.label}</span><strong>{category.passed}<small>/{category.total}</small></strong>
            <div className="evaluation-bar"><span style={{ width: `${category.total ? category.passed / category.total * 100 : 0}%` }} /></div>
          </article>
        ))}
      </div>
      <div className="evaluation-method">
        <div><span>SAFE FAILURE</span><strong>{evaluation.failed === 0 ? "No evaluation failures" : `${evaluation.failed} scenario failures`}</strong><p>GO is never forced when route, accessibility, facility availability or safe-window evidence is insufficient.</p></div>
        <div><span>CLAIM BOUNDARY</span><strong>POC validation, not field performance</strong><p>{evaluation.label}</p></div>
      </div>
      {evaluation.failures?.length > 0 && (
        <div className="failure-list"><strong>Failures to inspect</strong>{evaluation.failures.map((failure) => <div key={failure.id}><span>{failure.id}</span><p>{failure.expectation}</p><b>{failure.observed}</b></div>)}</div>
      )}
    </div>
  );
}

function App() {
  const [theme, setTheme] = useState("dark");
  const [snapshot, setSnapshot] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [analytics, setAnalytics] = useState(null);
  const [history, setHistory] = useState([]);
  const [judgeMode, setJudgeMode] = useState(false);
  const [judgeTab, setJudgeTab] = useState("proof");
  const [proof, setProof] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [ibmStatus, setIbmStatus] = useState(null);
  const [ibmRunning, setIbmRunning] = useState(false);
  const version = useRef(-1);
  const session = useRef(null);
  const retiredSessions = useRef(new Set());
  const lastAction = useRef(null);
  const token = () => sessionStorage.getItem("momentguard-token") || "";

  function accept(data, recovery = false) {
    if (retiredSessions.current.has(data.sessionId)) return;
    if (session.current !== data.sessionId) {
      if (session.current && data.stateVersion <= version.current && !recovery) return;
      if (session.current) retiredSessions.current.add(session.current);
      session.current = data.sessionId;
      version.current = -1;
    }
    if (data.stateVersion <= version.current) return;
    version.current = data.stateVersion;
    setSnapshot(data);
    if (lastAction.current !== data.recommendation.action) {
      setHistory((items) => [
        { action: data.recommendation.action, reason: data.recommendation.reason, time: new Date(data.updatedAt).toLocaleTimeString() },
        ...items,
      ].slice(0, 6));
      lastAction.current = data.recommendation.action;
    }
  }

  async function request(path, body) {
    try {
      const response = await fetch(`/api/${path}`, {
        method: body === undefined ? "GET" : "POST",
        headers: { "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}) },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.detail || "Request failed");
      if (data.stateVersion !== undefined) accept(data);
      setError("");
      return data;
    } catch (requestError) {
      setError(requestError.message);
      return null;
    }
  }

  async function runGraniteExplanation() {
    if (!ibmStatus?.configured || ibmRunning) return;
    setIbmRunning(true);
    const result = await request("ibm/explain", {});
    setIbmRunning(false);
    if (result?.verified) {
      await refreshProof();
      const status = await request("ibm/status");
      if (status) setIbmStatus(status);
    }
  }

  useEffect(() => {
    let socket;
    let retry;
    let stopped = false;
    request("state");
    request("experiments?seed=42&fans=30").then((data) => data && setAnalytics(data));
    request("ibm/status").then((data) => data && setIbmStatus(data));

    function connect() {
      socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/live`);
      socket.onopen = () => {
        if (stopped) return;
        if (token()) socket.send(JSON.stringify({ token: token() }));
        setConnected(true);
      };
      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.payload?.snapshot) accept(message.payload.snapshot, message.type === "snapshot");
      };
      socket.onerror = () => setConnected(false);
      socket.onclose = () => {
        if (stopped) return;
        setConnected(false);
        retry = setTimeout(connect, 1500);
      };
    }
    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      socket?.close();
    };
  }, []);

  useEffect(() => {
    if (!judgeMode || !snapshot?.stateVersion) return;
    const timer = setTimeout(() => { refreshProof(); }, 80);
    return () => clearTimeout(timer);
  }, [judgeMode, snapshot?.stateVersion]);

  const rec = snapshot?.recommendation;
  const state = snapshot?.state;
  const fan = snapshot?.fan;
  const accessible = fan?.accessible || false;
  const delivery = fan?.delivery || false;
  const action = rec?.action || "WAIT";
  const safeWindow = rec?.safeWindow || {};
  const currentNeed = fan?.need || "food";
  const bestFacility = snapshot?.facilities?.find((facility) => facility.id === rec?.destination);
  const availableSeconds = Math.max(0, Math.round((safeWindow.availableMinutes || 0) * 60));
  const requiredSeconds = Math.max(0, Math.round((safeWindow.requiredMinutes || 0) * 60));
  const marginSeconds = safeWindow.marginMinutes === null || safeWindow.marginMinutes === undefined ? null : Math.round(safeWindow.marginMinutes * 60);

  const statusCopy = {
    GO: { verb: "GO NOW", eyebrow: "SAFE TO MOVE", detail: "Your complete trip fits the current window." },
    WAIT: { verb: "WAIT", eyebrow: "HOLD FOR A BETTER WINDOW", detail: "MomentGuard is watching game and venue conditions." },
    STAY: { verb: "STAY", eyebrow: "PROTECT THIS MOMENT", detail: "The game state is too valuable to recommend leaving." },
    RETURN: { verb: "RETURN NOW", eyebrow: "MOMENT RECOVERY", detail: "Play resumed. Your route is being prioritized back to the seat." },
  }[action];

  const facilityLoads = useMemo(() => (snapshot?.facilities || []).map((facility) => ({
    ...facility,
    load: Math.min(100, Math.round(((facility.queue + 1) / Math.max(1, facility.capacity * 4)) * 100 * facility.congestion)),
  })), [snapshot]);

  function setNeed(need) {
    request("need", { need });
  }

  function setAccessible(value) {
    request("preferences", { accessible: value, delivery, speed: fan?.speed || 72 });
  }

  function setDelivery(value) {
    request("preferences", { accessible, delivery: value, speed: fan?.speed || 72 });
  }

  function orderToSeat() {
    const facility = rec?.bestAlternative?.facility || "food-north";
    if (!window.confirm("Place a simulated Arena Burger Combo order for $14.50 CAD? No payment is processed.")) return;
    request("orders", { facility, item: "burger", quantity: 1, mode: "delivery", confirmed: true });
  }

  async function refreshProof() {
    const data = await request("proof");
    if (data) setProof(data);
  }

  async function runEvaluation() {
    const data = await request("evaluation");
    if (data) setEvaluation(data);
  }

  function toggleJudgeMode() {
    const next = !judgeMode;
    setJudgeMode(next);
    if (next) {
      refreshProof();
      runEvaluation();
    }
  }

  return (
    <div className={`app theme-${theme}`}>
      <header className="topbar">
        <a href="#overview" className="brand" aria-label="MomentGuard AI home">
          <BrandMark />
          <span className="brand-copy"><strong>MomentGuard <b>AI</b></strong><small>FAN-CENTRIC AGENTIC EXPERIENCE</small></span>
        </a>
        <nav>
          <a href="#overview">Fan experience</a>
          <a href="#venue-intelligence">Venue intelligence</a>
          <a href="#technology">IBM architecture</a>
          {judgeMode && <a href="#proof-center">Proof center</a>}
        </nav>
        <div className="top-actions">
          <span className={connected ? "connection live" : "connection"}><i />{connected ? "LIVE SIMULATION" : "RECONNECTING"}</span>
          <button className={judgeMode ? "ghost-button active" : "ghost-button"} onClick={toggleJudgeMode}>Judge mode</button>
          <button className="icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme">{theme === "dark" ? "☼" : "☾"}</button>
        </div>
      </header>

      <main id="overview" className="page-shell">
        <section className="hero-copy">
          <div>
            <span className="kicker">IBM SKILLSBUILD · FAN-CENTRIC SPORTS & ENTERTAINMENT</span>
            <h1>Know when to go.<br/><span>Stay for what matters.</span></h1>
            <p>MomentGuard combines live game context, venue flow, fan needs and explainable decision logic to protect the moments fans came to see.</p>
          </div>
          <div className="challenge-badge"><span>POC</span><strong>Human-supervised</strong><small>Simulated data · auditable decisions</small></div>
        </section>

        {error && <div className="error-banner" role="alert"><strong>Connection issue</strong><span>{error}</span></div>}

        <section className="game-strip">
          <div className="match-team"><span className="team-badge tor">TOR</span><div><strong>Raptors</strong><small>HOME</small></div></div>
          <div className="match-score"><strong>{state?.scoreA ?? "—"}<span>:</span>{state?.scoreB ?? "—"}</strong><small>{state?.clock || "Connecting…"}</small></div>
          <div className="match-team away"><div><strong>Celtics</strong><small>AWAY</small></div><span className="team-badge bos">BOS</span></div>
          <div className="game-state"><span>GAME STATE</span><strong>{state?.gameState || "CONNECTING"}</strong><small>Illustrative matchup · not a live sports feed</small></div>
        </section>

        <section className={`decision-card action-${action.toLowerCase()}`}>
          <div className="decision-main">
            <span className="kicker">MOMENTGUARD DECISION</span>
            <div className="action-lockup"><span className="action-dot"/><h2>{statusCopy.verb}</h2></div>
            <p className="action-eyebrow">{statusCopy.eyebrow}</p>
            <p className="action-detail">{rec?.explanation || statusCopy.detail}</p>

            {action === "GO" && (
              <div className="safe-window-hero">
                <div><span>SAFE WINDOW</span><strong>{fmtMinutes(safeWindow.availableMinutes)}</strong></div>
                <div><span>TRIP NEEDS</span><strong>{fmtMinutes(safeWindow.requiredMinutes)}</strong></div>
                <div className="margin"><span>SAFETY MARGIN</span><strong>{marginSeconds >= 0 ? "+" : ""}{fmtMinutes(Math.abs((marginSeconds || 0) / 60))}</strong></div>
              </div>
            )}

            {action === "RETURN" && (
              <div className="recovery-card">
                <span>⚡ MOMENT RECOVERY ACTIVE</span>
                <strong>Play resumed while you were away.</strong>
                <p>{state?.scoreA}–{state?.scoreB}, {state?.clock}. MomentGuard has switched from destination routing to the fastest eligible return route.</p>
              </div>
            )}

            {rec?.bestAlternative && action !== "RETURN" && (
              <div className="alternative-card">
                <div><span className="kicker">SAFER ALTERNATIVE</span><strong>{rec.bestAlternative.title}</strong><p>{rec.bestAlternative.reason}</p></div>
                <div className="alternative-action"><span>ETA {fmtMinutes(rec.bestAlternative.estimatedMinutes)}</span><button onClick={orderToSeat}>Order to seat</button></div>
              </div>
            )}

            <div className="decision-actions">
              <button className="primary-button" disabled={action !== "GO"} onClick={() => request("trips/start", {})}>Start smart route</button>
              <button className="secondary-button" onClick={() => request("scenario", { scenario: action === "GO" ? "resumed" : "timeout" })}>{action === "GO" ? "Demo early resume" : "Find next window"}</button>
            </div>
            <p className="decision-foot">{action === "GO" ? `Return by approximately ${fmtTimeFromNow(safeWindow.requiredMinutes)} · ${bestFacility?.name || "best eligible destination"}` : statusCopy.detail}</p>
          </div>
          <RiskBreakdown items={rec?.riskBreakdown} score={rec?.riskScore || 0} />
        </section>

        <section className="need-section">
          <div className="section-title"><div><span className="kicker">WHAT DO YOU NEED?</span><h2>One tap. One decision.</h2></div><p>MomentGuard recomputes the safest option using your selected need and preferences.</p></div>
          <div className="need-grid">
            {Object.entries(needMeta).map(([key, meta]) => (
              <button key={key} className={currentNeed === key ? "need-card selected" : "need-card"} onClick={() => setNeed(key)}>
                <span className="need-icon">{meta.icon}</span><div><strong>{meta.label}</strong><small>{meta.helper}</small></div><b>→</b>
              </button>
            ))}
          </div>
        </section>

        <section className="experience-grid">
          <article className="surface map-surface">
            <VenueMap snapshot={snapshot} recommendation={rec} setNeed={setNeed} />
          </article>
          <aside className="surface preference-surface">
            <span className="kicker">PERSONALIZED FOR THE FAN</span>
            <h2>Preferences that change the route</h2>
            <p className="surface-copy">Accessibility and fulfillment preferences are decision inputs, not decorative filters.</p>
            <div className="preference-row">
              <div><span className="preference-symbol">♿</span><div><strong>Accessible routing</strong><small>Avoid inaccessible facilities and path segments</small></div></div>
              <button role="switch" aria-checked={accessible} className={accessible ? "switch on" : "switch"} onClick={() => setAccessible(!accessible)}><span /></button>
            </div>
            <div className="preference-row">
              <div><span className="preference-symbol">▣</span><div><strong>Seat delivery</strong><small>Offer delivery when leaving is the higher-risk choice</small></div></div>
              <button role="switch" aria-checked={delivery} className={delivery ? "switch on" : "switch"} onClick={() => setDelivery(!delivery)}><span /></button>
            </div>
            <div className="eligibility-card">
              <span>ROUTE ELIGIBILITY</span>
              <strong>{accessible ? "Accessible graph active" : "Standard graph active"}</strong>
              <p>{accessible ? "Inaccessible edges and facilities are removed before routing." : "Turn on accessible routing to see the graph change immediately."}</p>
            </div>
            <div className="order-list">
              {(snapshot?.orders || []).slice(-2).reverse().map((order) => (
                <div key={order.id}><span>SIMULATED ORDER</span><strong>{order.item} · {order.mode}</strong><small>{order.status.replaceAll("_", " ")}</small></div>
              ))}
            </div>
          </aside>
        </section>

        <section id="venue-intelligence" className="section-block">
          <div className="section-title"><div><span className="kicker">B2B VALUE · VENUE INTELLIGENCE</span><h2>Optimize the arena, not just the individual.</h2></div><p>CrowdFlow predicts collective demand so one timeout does not send every fan to the same concession.</p></div>
          <div className="venue-intelligence-grid">
            <article className="surface flow-surface">
              <div className="surface-heading"><div><span className="kicker">LIVE FAN FLOW</span><h3>Concourse pressure</h3></div><span className="pill neutral">CURRENT SIMULATION</span></div>
              <div className="load-list">
                {facilityLoads.map((facility) => (
                  <div className="load-row" key={facility.id}>
                    <div><strong>{facility.name}</strong><small>{facility.open ? `${facility.queue} waiting · ${facility.need}` : "Closed"}</small></div>
                    <div className="load-bar"><span style={{ width: `${facility.open ? facility.load : 0}%` }} /></div>
                    <b>{facility.open ? pct(facility.load) : "OFF"}</b>
                  </div>
                ))}
              </div>
              <div className="operator-note"><span>WHY A VENUE BUYS THIS</span><p>Better demand distribution, fewer queue spikes, more actionable concession intelligence and a fan experience tied directly to game context.</p></div>
            </article>
            <article className="surface impact-surface">
              <ImpactCard analytics={analytics} />
            </article>
          </div>
        </section>

        <section id="technology" className="section-block">
          <div className="section-title"><div><span className="kicker">IBM CLOUD + EXPLAINABLE AI</span><h2>Granite explains. Deterministic tools keep final authority.</h2></div><p>MomentGuard can call IBM watsonx.ai on IBM Cloud for a grounded explanation while GO / WAIT / STAY / RETURN remain controlled by the tested safety engine.</p></div>
          <div className="architecture-flow">
            <article><span>01</span><div className="arch-icon">G</div><h3>Game Intelligence</h3><p>Derives an explainable Moment Risk score from score, clock, pause state and event context.</p><small className="status-chip active">LOCAL TOOL ACTIVE</small></article>
            <i>→</i>
            <article><span>02</span><div className="arch-icon">V</div><h3>Venue Intelligence</h3><p>Evaluates routes, queue load, accessibility, service time and closures.</p><small className="status-chip active">LOCAL TOOL ACTIVE</small></article>
            <i>→</i>
            <article><span>03</span><div className="arch-icon">G</div><h3>watsonx.ai · Granite</h3><p>Generates a grounded fan-facing explanation after the deterministic decision is finalized.</p><small className={ibmStatus?.configured ? "status-chip active" : "status-chip ready"}>{ibmStatus?.configured ? "IBM CLOUD CONFIGURED" : "ADD CLOUD CREDENTIALS"}</small></article>
            <i>→</i>
            <article><span>04</span><div className="arch-icon">M</div><h3>MomentGuard Safety</h3><p>Validates session, version, destination and action before any agent proposal can influence the UI.</p><small className="status-chip active">GUARDRAILS ACTIVE</small></article>
          </div>
          <div className="ibm-proof-row">
            <div><span className="kicker">IBM BOB</span><strong>Repository-aware development workflow</strong><p>Project-specific Bob agent context and evidence are preserved in `.bob/` and `bob_sessions/` for the submission.</p></div>
            <div><span className="kicker">IBM CLOUD · GRANITE</span><strong>{ibmStatus?.configured ? "Runtime configured" : "Explanation layer ready"}</strong><p>{ibmStatus?.configured ? `watsonx.ai is configured for ${ibmStatus.model || "the selected Granite model"}. Run it in Proof Center to create a verified trace.` : "Add the team's watsonx credentials server-side, then run one explanation from Proof Center."}</p></div>
            <div><span className="kicker">AUDITABILITY</span><strong>Every decision has evidence</strong><p>Risk breakdown, route calculation, safety buffer, event history and agent trace are inspectable.</p></div>
          </div>
        </section>

        {judgeMode && (
          <section className="judge-panel">
            <div className="surface-heading judge-heading"><div><span className="kicker">JUDGE MODE</span><h3>Evidence before claims.</h3></div><button className="ghost-button" onClick={() => request("reset", {}).then(() => refreshProof())}>Reset demo</button></div>
            <div className="judge-tabs" role="tablist" aria-label="Judge mode sections">
              <button className={judgeTab === "proof" ? "active" : ""} onClick={() => { setJudgeTab("proof"); refreshProof(); }}>Proof Center</button>
              <button className={judgeTab === "evaluation" ? "active" : ""} onClick={() => { setJudgeTab("evaluation"); runEvaluation(); }}>Evaluation Lab</button>
              <button className={judgeTab === "demo" ? "active" : ""} onClick={() => setJudgeTab("demo")}>Demo Controls</button>
            </div>

            {judgeTab === "proof" && <ProofCenter proof={proof} analytics={analytics} onRefresh={refreshProof} onRunGranite={runGraniteExplanation} ibmRunning={ibmRunning} ibmStatus={ibmStatus} />}
            {judgeTab === "evaluation" && <EvaluationLab evaluation={evaluation} onRun={runEvaluation} />}
            {judgeTab === "demo" && (
              <div className="demo-controls-panel">
                <div className="scenario-controls">
                  {scenarios.map(([key, label, helper]) => <button key={key} className={state?.scenario === key ? "scenario-control active" : "scenario-control"} onClick={() => request("scenario", { scenario: key }).then(() => refreshProof())}><strong>{label}</strong><small>{helper}</small></button>)}
                </div>
                <div className="judge-actions">
                  <button onClick={() => request("simulation/tick", { seconds: 30 }).then(() => refreshProof())}>Advance 30 seconds</button>
                  <button onClick={() => request("simulation/auto", { enabled: !snapshot?.automatic })}>{snapshot?.automatic ? "Pause" : "Start"} auto progression</button>
                  {bestFacility && <button onClick={() => request(`facilities/${bestFacility.id}`, { queue: bestFacility.queue + 10 }).then(() => refreshProof())}>Spike recommended queue</button>}
                  {bestFacility && <button onClick={() => request(`facilities/${bestFacility.id}`, { open: !bestFacility.open }).then(() => refreshProof())}>{bestFacility.open ? "Close" : "Reopen"} destination</button>}
                  <button onClick={async () => { const data = await request("experiments?seed=42&fans=30"); if (data) setAnalytics(data); }}>Rerun 30-fan benchmark</button>
                </div>
                <div className="judge-evidence">
                  <div><span>TRIP STATUS</span><strong>{fan?.trip?.status || "At seat"}</strong></div>
                  <div><span>DESTINATION</span><strong>{bestFacility?.name || "None"}</strong></div>
                  <div><span>STATE VERSION</span><strong>{snapshot?.stateVersion ?? "—"}</strong></div>
                  <div><span>IBM TRACE</span><strong>{proof?.ibmExecution?.verified ? "Verified" : "Unverified · honest fallback"}</strong></div>
                </div>
              </div>
            )}
          </section>
        )}

        <section className="decision-history">
          <div className="section-title compact"><div><span className="kicker">AUDIT TRAIL</span><h2>Recent decisions</h2></div><button className="text-button" onClick={() => setHistory([])}>Clear</button></div>
          <div className="history-list">
            {history.length ? history.map((item, index) => (
              <div key={`${item.time}-${index}`} className="history-item"><span className={`mini-status ${item.action.toLowerCase()}`}>{item.action}</span><p>{item.reason}</p><time>{item.time}</time></div>
            )) : <p className="empty-state">Interact with the simulation to build an auditable decision trail.</p>}
          </div>
        </section>

        <section className="closing-cta">
          <div><span className="kicker">MOMENTGUARD AI</span><h2>Leave smarter. Miss nothing that matters.</h2><p>Fan experience intelligence that connects the game, the venue and the person in the seat.</p></div>
          <button className="primary-button" onClick={() => { window.scrollTo({ top: 0, behavior: "smooth" }); request("scenario", { scenario: "timeout" }); }}>Find my next window →</button>
        </section>
      </main>

      <footer><div><BrandMark/><strong>MomentGuard AI</strong></div><p>IBM SkillsBuild Hackathon 2026 · Team Asma, Ayaan, Sayali · Fictional venue and simulated data only</p><span>© 2026 MomentGuard AI</span></footer>
    </div>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error('Cannot start MomentGuard AI: index.html is missing <div id="root"></div>.');
createRoot(root).render(<StrictMode><App /></StrictMode>);
