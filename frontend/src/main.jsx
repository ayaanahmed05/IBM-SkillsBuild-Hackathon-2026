import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const scenarios = {
  timeout: {
    status: "WAIT",
    title: "The game is about to resume.",
    message: "A timeout is underway. Check nearby queues, but keep your trip short.",
    clock: "02:41",
    quarter: "Q4",
    queue: 8,
    crowd: "Moderate",
    walk: 3,
    reason: "Timeout detected · Short trip available",
  },
  critical: {
    status: "STAY",
    title: "Stay close to the action.",
    message: "A critical possession is approaching. Delay nonessential trips.",
    clock: "00:38",
    quarter: "Q4",
    queue: 11,
    crowd: "High",
    walk: 4,
    reason: "Critical possession · High return risk",
  },
  steady: {
    status: "GO",
    title: "A good window for a quick trip.",
    message: "Game pace is steady. A nearby concession or restroom trip may fit.",
    clock: "06:18",
    quarter: "Q3",
    queue: 4,
    crowd: "Low",
    walk: 2,
    reason: "Stable pace · Short queue · Nearby location",
  },
  resumed: {
    status: "RETURN NOW",
    title: "Head back before the next big moment.",
    message: "Play has resumed. Prioritize returning to your seat.",
    clock: "02:12",
    quarter: "Q4",
    queue: 7,
    crowd: "Moderate",
    walk: 3,
    reason: "Play resumed · Seat return prioritized",
  },
};

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
  const [scenarioKey, setScenarioKey] = useState("timeout");
  const [destination, setDestination] = useState("Food");
  const [accessible, setAccessible] = useState(false);
  const [delivery, setDelivery] = useState(false);
  const [activeNav, setActiveNav] = useState("Overview");
  const [history, setHistory] = useState([
    { status: "WAIT", note: "Timeout detected", time: "12:42 PM" },
    { status: "GO", note: "Short queue available", time: "12:39 PM" },
    { status: "STAY", note: "Critical possession", time: "12:34 PM" },
  ]);

  const current = scenarios[scenarioKey];

  function changeScenario(key) {
    setScenarioKey(key);
    setHistory((items) => [
      {
        status: scenarios[key].status,
        note: scenarioLabels.find(([id]) => id === key)?.[1] || key,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
      ...items,
    ].slice(0, 5));
  }

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
          <div className="live-label"><i /> LIVE </div>
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
                <div className="score">98 <span>—</span> 96</div>
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
            <span>Decision confidence <strong>{scenarioKey === "critical" ? "96%" : scenarioKey === "timeout" ? "94%" : scenarioKey === "resumed" ? "91%" : "87%"}</strong></span>
            <span className="simulation-note"> ESTIMATE</span>
          </div>
          <div className="progress-track"><div style={{ width: `${scenarioKey === "critical" ? 96 : scenarioKey === "timeout" ? 94 : scenarioKey === "resumed" ? 91 : 87}%` }} /></div>
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
              {delivery && destination === "Food" && <div className="delivery-note">Food-to-seat alternative selected. Ordering is not connected.</div>}
            </div>
          </section>
        </div>

        <section className="panel agents-panel" id="insights">
          <div className="section-heading">
            <div><div className="eyebrow">BEHIND THE RECOMMENDATION</div><h2>Agent workflow</h2><p>A transparent view of how the simulated decision is assembled.</p></div>
            <span className="workflow-pill"><i /> Workflow preview</span>
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
