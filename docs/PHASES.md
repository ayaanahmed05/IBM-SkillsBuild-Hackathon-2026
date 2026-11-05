# Phase verification and remaining work

| Phase | Implemented | Remaining / qualification |
|---|---|---|
| 1 | Source audit, modular FastAPI, original routes, CORS/proxy, environment, regression tests | Response keys retained with documented deliberate safety corrections; Node reference retained |
| 2 | Single runtime, game/pause clock, scores/possession context, seed scenarios, graph venue, fan/trip state, immutable-by-application event records, manual/automatic controls | Rich significant-event/score generator, spatial occupancy and crash recovery |
| 3 | Versioned snapshot-bearing events, WebSocket heartbeat/reconnect, immediate UI changes | Larger-scale backpressure/load testing |
| 4 | Deterministic risk, routing, queue/service/buffer, accessible eligibility and four actions | More detailed waypoint progress and safe-window forecasting |
| 5 | Official IBM docs reviewed; hosted typed Python tool and coordinator/specialist definition generator | Account capability verification, ADK validation/import, real delegation/tool proof, API transport, Granite entitlement, three further specialists |
| 6 | Nonblocking evaluation boundary, material/manual triggers, timeout/error/stale/unsafe validation, persisted local fallback traces | Wire actual verified IBM transport and persist its full real tool traces; debounce/backoff |
| 7 | Multi-fan records, demand-aware proposed assignments, spike/closure/reroute controls | Execute distributed plans as a batch, measure capacity shared across active trips, realistic congestion dynamics |
| 8 | Simulated catalog, prices, explicit confirmation, pickup/delivery timer, cancellation, trip phases | More items, per-fan ownership, order-linked trip orchestration |
| 9 | Provider protocols and simulated adapters; explicit provenance | Actual external provider intentionally absent; adapters not yet injected into runtime |
| 10 | Persisted runtime phase measurements; deterministic cohort estimate and repeatable command | Full dynamic matched-policy experiments, moment counts/protected comparison, utilization timeseries and richer measured metrics |
| 11 | Existing visual styling retained; API/WS, reasons/options, trip/order/trace/analytics controls | Richer multi-fan UI, accessible route drawing, automated browser regression suite |
| 12 | Executed Pytest and production build; manual browser check | Actual IBM tests, container run and larger concurrency/load testing |
| 13 | Audit, architecture/setup/API/config/limits/provenance/demo and honest IBM/Bob status | Real IBM trace and Bob evidence require actual tools/accounts |

The full thirteen-phase definition of done is not claimed. Offline end-to-end functionality is the delivered milestone. Cloud integration and the remaining measured simulation sophistication remain visible work.
