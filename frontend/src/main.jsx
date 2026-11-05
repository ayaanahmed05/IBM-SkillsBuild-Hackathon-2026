import { StrictMode, useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const scenarioLabels = [
  ["timeout", "Timeout"],
  ["critical", "Critical play"],
  ["steady", "Steady game"],
  ["resumed", "Play resumed"],
];

const agents = [
  {
    number: "01",
    name: "Game Intelligence",
    detail: "Interprets the game situation",
    icon: "◉",
  },
  {
    number: "02",
    name: "Venue Flow",
    detail: "Estimates queues and walking time",
    icon: "⌖",
  },
  {
    number: "03",
    name: "Fan Preferences",
    detail: "Applies the selected fan needs",
    icon: "♙",
  },
  {
    number: "04",
    name: "MomentGuard",
    detail: "Combines signals into a recommendation",
    icon: "✳",
  },
];

function App() {
  const [theme, setTheme] = useState("dark");
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [activeNav, setActiveNav] = useState("Overview");
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const version = useRef(-1);
  const lastAction = useRef(null);
  const session = useRef(null);
  const retiredSessions = useRef(new Set());
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
    const action = data.recommendation.action;
    if (lastAction.current !== action) {
      setHistory(items => [{status: action, note: data.recommendation.reason, time: new Date(data.updatedAt).toLocaleTimeString()}, ...items].slice(0, 8));
      lastAction.current = action;
    }
  }
  async function request(path, body) {
    try {
      const response = await fetch(`/api/${path}`, {method: body === undefined ? "GET" : "POST", headers: {"Content-Type": "application/json", ...(token() ? {Authorization: `Bearer ${token()}`} : {})}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.detail || "Request failed");
      if (data.stateVersion !== undefined) accept(data);
      setError("");
      return data;
    } catch (e) { setError(e.message); }
  }
  useEffect(() => {
    let socket, retry, stopped = false;
    request("state");
    function connect() {
      socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/live`);
      socket.onopen = () => { if (stopped) return; if (token()) socket.send(JSON.stringify({token: token()})); setConnected(true); };
      socket.onmessage = event => { const message = JSON.parse(event.data); if (message.payload?.snapshot) accept(message.payload.snapshot, message.type === "snapshot"); };
      socket.onerror = () => setConnected(false);
      socket.onclose = () => { if (stopped) return; setConnected(false); if (!stopped) retry = setTimeout(connect, 1500); };
    }
    connect();
    return () => { stopped = true; clearTimeout(retry); socket?.close(); };
  }, []);
  const scenarioKey = snapshot?.state.scenario || "critical";
  const destination = {food: "Food", restroom: "Restroom", shop: "Shop"}[snapshot?.fan.need || "food"];
  const accessible = snapshot?.fan.accessible || false;
  const delivery = snapshot?.fan.delivery || false;
  const rec = snapshot?.recommendation;
  const current = {status: rec?.action || "WAIT", title: rec?.title || "Connecting to MomentGuard…", message: rec?.explanation || "Waiting for backend state", reason: rec?.reason || "No state received", clock: snapshot?.state.clock.split(" · ")[1] || "—", quarter: `Q${snapshot?.state.quarter || "—"}`, queue: rec?.tripEstimate.queueMinutes ?? "—", walk: rec?.tripEstimate.walkMinutes ?? "—", crowd: Math.max(...(snapshot?.facilities.map(f => f.queue) || [0])) > 10 ? "High" : "Moderate"};
  function changeScenario(key) { request("scenario", {scenario: key}); }
  function setDestination(value) { request("need", {need: value.toLowerCase()}); }
  function setAccessible(value) { request("preferences", {accessible: value, delivery, speed: snapshot.fan.speed}); }
  function setDelivery(value) { request("preferences", {accessible, delivery: value, speed: snapshot.fan.speed}); }

  function goTo(section) {
    setActiveNav(section);
    document.getElementById(section.toLowerCase().replaceAll(" ", "-"))
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className={`app theme-${theme}`}>
      <header className="topbar">
        <a className="brand" href="#overview" aria-label="FanFlow AI home">
          <span className="brand-mark">✳</span>
          <span className="brand-text">
            <strong>FanFlow <span>AI</span></strong>
            <small>MOMENTGUARD</small>
          </span>
        </a>

        <nav className="nav-links" aria-label="Main navigation">
          {["Overview", "Venue Map", "Insights"].map((item) => (
            <button
              key={item}
              className={activeNav === item ? "nav-link selected" : "nav-link"}
              onClick={() => goTo(item)}
            >
              {item}
            </button>
          ))}
        </nav>

        <div className="top-actions">
          
          <button
            className="theme-toggle"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? "☼" : "☾"}
          </button>
          {/* <div className="user-avatar" aria-label="Fan profile">F</div> */}
        </div>
      </header>

      <main className="container" id="overview">
        <section className="welcome">
          <div>
            <div className="eyebrow">FAN EXPERIENCE <span>/</span> GAME DAY</div>
            <h1>Never miss <span>the moment.</span></h1>
            <p>Your intelligent game-day companion. Less waiting, smarter moves, more time in the action.</p>
          </div>
          <div className="live-label"><i /> {connected ? "SIMULATED · CONNECTED" : "SIMULATED · RECONNECTING"} </div>
        </section>

        <section className="game-banner">
          <div className="game-main">
            <div className="eyebrow">◉ FEATURED MATCHUP</div>
            <div className="matchup">
              <div className="team">
                <div className="team-logo raptors">TOR</div>
                <div><strong>Raptors</strong><small>HOME</small></div>
              </div>
              <div className="score-block">
                <div className="score">{snapshot?.state.scoreA ?? "—"} <span>—</span> {snapshot?.state.scoreB ?? "—"}</div>
                <div className="clock">{current.quarter} · {current.clock}</div>
              </div>
              <div className="team away">
                <div><strong>Celtics</strong><small>AWAY</small></div>
                <div className="team-logo celtics">BOS</div>
              </div>
            </div>
          </div>
          <div className="game-context">
            <div className="muted-label">GAME CONTEXT</div>
            <div className="context-value"><i /> {current.status === "WAIT" ? "Timeout in progress" : scenarioLabels.find(([key]) => key === scenarioKey)?.[1]}</div>
            <p>Illustrative game · No live feed connected</p>
          </div>
        </section>

        <section className="recommendation panel">
          <div className="recommendation-top">
            <div className="eyebrow">✳ MOMENTGUARD RECOMMENDATION</div>
            <span className={`status status-${current.status.toLowerCase().replaceAll(" ", "-")}`}>
              <i /> {current.status}
            </span>
          </div>
          <h2>{current.title}</h2>
          <p className="recommendation-message">{current.message}</p>

          <div className="reason-box">
            <span className="reason-icon">✧</span>
            <div><strong>Why this recommendation?</strong><p>{current.reason}</p></div>
          </div>

          <div className="confidence-row">
            <span>Moment risk score <strong>{rec?.riskScore ?? "—"} / 100</strong></span>
            <span className="simulation-note"> HEURISTIC</span>
          </div>
          <div className="progress-track"><div style={{ width: `${rec?.riskScore || 0}%` }} /></div>
        </section>

        {error && <div role="alert" className="reason-box">{error}</div>}
        <section className="panel runtime-controls">
          <div className="section-heading"><h2>Simulation and trip controls</h2><span>All orders and data are simulated</span></div>
          <button onClick={() => request("simulation/auto", {enabled: !snapshot?.automatic})}>{snapshot?.automatic ? "Pause" : "Start"} automatic progression</button>
          <button onClick={() => request("simulation/tick", {seconds: 30})}>Advance 30 seconds</button>
          <button onClick={() => request("reset", {})}>Reset simulation</button>
          <button disabled={current.status !== "GO"} onClick={() => request("trips/start", {})}>Start recommended trip</button>
          <p>Trip: {snapshot?.fan.trip?.status || "At seat"} · Destination: {rec?.destination || "None eligible"} · Complete estimate: {rec?.roundTripMinutes ?? "—"} min</p>
          <p>Calculation: walk out + queue + service + return walk + safety buffer. Available window: {snapshot?.state.availableWindowMinutes?.toFixed(1) || "0"} min.</p>
          <div className="facility-options">{snapshot?.facilities.map(f => <div key={f.id}>
            <strong>{f.name}</strong> · {f.queue} waiting · {f.open ? "Open" : "Closed"}
            <button onClick={() => request(`facilities/${f.id}`, {queue: f.queue + 10})}>Queue spike</button>
            <button onClick={() => request(`facilities/${f.id}`, {open: !f.open})}>{f.open ? "Close" : "Reopen"}</button>
          </div>)}</div>
          {rec?.calculation && <p>Route: {rec.calculation.route.path.join(" → ")}</p>}
          <button onClick={() => { if (window.confirm("Confirm simulated water order for $3 CAD? No payment is processed.")) request("orders", {facility: "food-north", item: "water", mode: delivery ? "delivery" : "pickup", confirmed: true}); }}>Confirm simulated water order · $3</button>
          {snapshot?.orders.map(o => <p key={o.id}>SIMULATED {o.item} · {o.mode} · {o.status} {o.status === "preparing" && <button onClick={() => request(`orders/${o.id}/cancel`, {})}>Cancel</button>}</p>)}
          <button onClick={async () => { const data = await request("experiments?seed=42&fans=30"); if (data) setAnalytics(data); }}>Run reproducible experiment</button>
          {analytics && <pre className="trace-output">{JSON.stringify(analytics.runs && Object.fromEntries(Object.entries(analytics.runs).map(([k,v]) => [k,v.metrics])), null, 2)}</pre>}
          <h3>Actual evaluation trace</h3>
          {snapshot?.agents.length ? snapshot.agents.map((t,i) => <p key={i}>{t.provider} · {t.summary} · {t.latencyMs} ms</p>) : <p>No agent evaluations recorded. IBM has not been invoked.</p>}
        </section>

        <section className="scenario-section">
          <div className="section-heading">
            <div><div className="eyebrow">TRY THE EXPERIENCE</div><h2>Game-day scenarios</h2></div>
            {/* <span className="subtle-tag">Interactive simulation</span> */}
          </div>
          <div className="scenario-grid">
            {scenarioLabels.map(([key, label]) => (
              <button
                key={key}
                className={`scenario-card ${scenarioKey === key ? "scenario-active" : ""}`}
                onClick={() => changeScenario(key)}
                aria-pressed={scenarioKey === key}
              >
                <span className="scenario-icon">{key === "timeout" ? "Ⅱ" : key === "critical" ? "ϟ" : key === "steady" ? "↗" : "⌂"}</span>
                <span className="scenario-label">{label}</span>
                <span className="scenario-arrow">↗</span>
              </button>
            ))}
          </div>
        </section>

        <section className="metrics-grid" aria-label="Venue metrics">
          <div className="metric-card"><div className="metric-top"><span>♨</span><small>QUEUE ESTIMATE</small></div><strong>{current.queue} <em>min</em></strong><p>Nearby concessions</p><span className="metric-bottom">◷ 
            Estimate</span></div>
          <div className="metric-card"><div className="metric-top"><span>♙</span><small>CROWD LEVEL</small></div><strong>{current.crowd}</strong><p>Concourse activity</p><span className="metric-bottom"><i className="tiny-dot" /> Based on scenario</span></div>
          <div className="metric-card"><div className="metric-top"><span>⌖</span><small>WALKING TIME</small></div><strong>{current.walk} <em>min</em></strong><p>From your current section</p><span className="metric-bottom">⇢ Estimated route</span></div>
          <div className="metric-card"><div className="metric-top"><span>✳</span><small>YOUR DESTINATION</small></div><strong className="destination-value">{destination}</strong><p>Personalized trip planning</p><span className="metric-bottom">✓ Preference applied</span></div>
        </section>

        <div className="main-columns">
          <section className="panel venue-panel" id="venue-map">
            <div className="section-heading">
              <div><div className="eyebrow">EXPLORE YOUR VENUE</div><h2>Venue map</h2><p>Illustrative arena layout · Not to scale</p></div>
              <span className="map-tag">LEVEL 1</span>
            </div>

            <div className="arena">
              <div className="arena-label arena-top-label">NORTH CONCOURSE</div>
              <div className="arena-ring">
                <div className="court">
                  <div className="court-circle" />
                  <div className="court-line" />
                  <span>COURT</span>
                </div>
                <button className={`map-pin pin-food ${destination === "Food" ? "pin-selected" : ""}`} onClick={() => setDestination("Food")} aria-label="Select food concession">♨<small>FOOD</small></button>
                <button className={`map-pin pin-restroom ${destination === "Restroom" ? "pin-selected" : ""}`} onClick={() => setDestination("Restroom")} aria-label="Select restroom">♧<small>WC</small></button>
                <button className={`map-pin pin-shop ${destination === "Shop" ? "pin-selected" : ""}`} onClick={() => setDestination("Shop")} aria-label="Select fan shop">▧<small>SHOP</small></button>
                <div className="you-are-here"><span /><small>YOU</small></div>
              </div>
              <div className="arena-label arena-bottom-label">SOUTH CONCOURSE</div>
            </div>

            <div className="map-legend">
              <span><i className="legend-blue" /> Food</span><span><i className="legend-green" /> Restroom</span><span><i className="legend-purple" /> Shop</span><span><i className="legend-white" /> You</span>
            </div>

            {/* <div className="destination-summary">
              <div><span className="destination-icon">⌖</span><div><strong>{destination} destination selected</strong><p>Approx. {current.walk} minutes walking time</p></div></div>
              <button className="text-button" onClick={() => setDestination(destination === "Food" ? "Restroom" : destination === "Restroom" ? "Shop" : "Food")}>Change destination ↗</button>
            </div> */}
          </section>

          <section className="panel preferences-panel">
            <div className="section-heading">
              <div><div className="eyebrow">MADE FOR YOU</div><h2>Fan preferences</h2><p>Shape your game-day experience.</p></div>
            </div>

            <label className="field-label" htmlFor="destination">I'm heading to</label>
            <select id="destination" value={destination} onChange={(event) => setDestination(event.target.value)}>
              <option>Food</option><option>Restroom</option><option>Shop</option>
            </select>

            <div className="preference-toggle">
              <div className="preference-icon">♿</div>
              <div className="preference-copy"><strong>Accessible routing</strong><p>Prioritize accessible paths</p></div>
              <button className={`switch ${accessible ? "switch-on" : ""}`} role="switch" aria-checked={accessible} onClick={() => setAccessible(!accessible)}><span /></button>
            </div>
            <div className="preference-toggle">
              <div className="preference-icon">♨</div>
              <div className="preference-copy"><strong>Food-to-seat</strong><p>Explore delivery alternatives</p></div>
              <button className={`switch ${delivery ? "switch-on" : ""}`} role="switch" aria-checked={delivery} onClick={() => setDelivery(!delivery)}><span /></button>
            </div>

            {(accessible || delivery) && <div className="personalization-note">{accessible && <p>✓ Accessible route preference enabled</p>}{delivery && <p>✓ Food-to-seat alternative enabled</p>}</div>}

            <div className="trip-card">
              <div className="trip-card-header"><span>✳ YOUR TRIP PLAN</span></div>
              <div className="trip-destination"><span className="trip-icon">⌖</span><div><strong>{destination}</strong><p>{accessible ? "Accessible route preference" : "Standard estimated route"}</p></div></div>
              <div className="trip-stats"><div><small>WALK</small><strong>{current.walk} min</strong></div><div><small>QUEUE</small><strong>{current.queue} min</strong></div><div><small>CROWD</small><strong>{current.crowd}</strong></div></div>
              {delivery && destination === "Food" && <div className="delivery-note">Simulated delivery available at North Concessions. Confirm an order below.</div>}
            </div>
          </section>
        </div>

        <section className="panel agents-panel" id="insights">
          <div className="section-heading">
            <div><div className="eyebrow">BEHIND THE RECOMMENDATION</div><h2>Agent workflow</h2><p>Deterministic tools are active. IBM execution is unverified until account setup and a real invocation succeed.</p></div>
            <span className="workflow-pill"><i /> Specialist responsibilities</span>
          </div>
          <div className="agent-flow">
            {agents.map((agent, index) => (
              <div className="agent-wrap" key={agent.number}>
                <article className="agent-card">
                  <div className="agent-card-top"><span className="agent-number">{agent.number}</span><span className="agent-symbol">{agent.icon}</span></div>
                  <h3>{agent.name}</h3><p>{agent.detail}</p>
                  {/* <div className="agent-state"><i /> SIMULATED</div> */}
                </article>
                {index < agents.length - 1 && <div className="flow-arrow" aria-hidden="true">→</div>}
              </div>
            ))}
          </div>
          {/* <div className="workflow-disclaimer">This is a frontend simulation. Agent orchestration, live game feeds, venue APIs, and backend integration are not connected yet.</div> */}
        </section>

        <section className="panel history-panel">
          <div className="section-heading">
            <div><div className="eyebrow">DECISION TRACE</div><h2>Recent recommendations</h2><p>Explore the most recent scenario changes.</p></div>
            <button className="text-button" onClick={() => setHistory([])}>Clear history ×</button>
          </div>
          {history.length === 0 ? <div className="empty-history">Your scenario history is empty. Choose a game-day scenario above to create a new entry.</div> : (
            <div className="history-list">
              {history.map((item, index) => <div className="history-row" key={`${item.time}-${index}`}>
                <span className={`history-status history-${item.status.toLowerCase().replaceAll(" ", "-")}`}>{item.status}</span>
                <span className="history-note">{item.note}</span>
                <span className="history-time">{item.time}</span>
              </div>)}
            </div>
          )}
        </section>

        <section className="closing-banner">
          <div className="closing-symbol">✳</div>
          <div><h2>Your game. Your moment.</h2><p>Less time waiting in line. More time where it matters.</p></div>
          <button onClick={() => { goTo("Overview"); changeScenario("steady"); }}>Find my next window <span>→</span></button>
        </section>
      </main>

      <footer className="footer">
        <a className="footer-brand" href="#overview">✳ FANFLOW AI <span>· MOMENTGUARD</span></a>
       
        <p className="team-credit">Team: Asma, Ayaan, Sayali</p>
        <p className="copyright">© 2026 FanFlow AI</p>
      </footer>
    </div>
  );
}

const root = document.getElementById("root");

if (!root) {
  throw new Error('Cannot start FanFlow AI: index.html is missing <div id="root"></div>.');
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);
