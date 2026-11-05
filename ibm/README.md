# IBM integration status: not provisioned or verified

No IBM execution is claimed. The local application uses deterministic fallback. The adapter boundary in backend/app/agents.py tests proposal validation, staleness, timeouts and authentication failures; it is not an IBM transport. `/api/agents` reports this explicitly. No Granite model availability has been assumed.

## Verify account capabilities first

In your actual provisioned IBM account, identify Orchestrate instance URL, hosting type, allowed authentication and permission to import Python tools/native agents. Inspect available model IDs; choose Granite only if actually listed. watsonx.ai access is separate and is not required for the offline demo. Do not commit keys or paste them into logs.

Official references reviewed during implementation:
- [Remote environment authentication](https://developer.watson-orchestrate.ibm.com/environment/initiate_environment)
- [Python tools and typed schemas](https://developer.watson-orchestrate.ibm.com/tools/create_tool)
- [Native agents and collaborators](https://developer.watson-orchestrate.ibm.com/agents/build_agent)

## Smallest cloud proof

Install ADK in a separate virtualenv using requirements.txt. Follow the version of IBM documentation matching your installed ADK (the docs now distinguish 1.x and 2.x). Register the actual instance with `orchestrate env add -n skillsbuild -u <instance-url>`, then `orchestrate env activate skillsbuild` and enter the key at the interactive prompt. List agents/tools and available models in your actual environment. Authentication and model entitlement must succeed before deployment is claimed.

Generate candidate definitions with `python ibm/generate_agents.py --model <verified-model-id>`. Review style against your installed ADK. Import `snapshot_tools.py` as a Python tool with its requirements, then import game_intelligence before momentguard_coordinator. These artifacts have not been validated by the ADK or imported into IBM here.

Supply a current application snapshot to the coordinator. Require a specialist delegation and a calculate_moment_risk invocation; inspect IBM's actual execution trace. Save a redacted trace with agent/tool names, validated inputs/outputs, timestamps, latency and actual cloud result. Then implement a transport for the verified account API and wire it into evaluate(). Only label execution IBM after this succeeds. The remaining Venue Intelligence, Fan Experience and CrowdFlow cloud agents should follow that proof, not precede it.

The hosted tool consumes supplied typed context and needs no access to localhost. No development API tunnel is provided. If API tools are later deployed, use HTTPS and authentication. A cloud result must match the current session/version and pass deterministic validation before influencing the UI. The initial proof only supplies explanation; it cannot place orders or change the game.

## Responsibility boundaries

Coordinator delegates and proposes. Game Intelligence calculates game risk. Venue Intelligence will invoke facility/routing calculations. Fan Experience will apply need and fulfillment preferences. CrowdFlow will evaluate additional demand. Only the first two have candidate cloud definitions; the latter three currently exist as deterministic application functions, not IBM agents.
