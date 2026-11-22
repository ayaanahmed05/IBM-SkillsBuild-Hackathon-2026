"""Judge-facing evidence builder for MomentGuard decisions."""
from .engine import route


def _ibm_execution(runtime):
    traces = list(runtime.traces)
    verified = [
        trace for trace in traces
        if trace.get('success') and str(trace.get('provider', '')).lower().startswith(('ibm', 'watsonx'))
    ]
    latest = verified[-1] if verified else None
    if latest:
        return {
            'verified': True,
            'status': 'Verified IBM runtime execution',
            'provider': latest.get('provider'),
            'latencyMs': latest.get('latencyMs'),
            'trace': latest,
            'model': latest.get('model'),
            'explanation': (latest.get('output') or {}).get('explanation'),
            'steps': [
                {'label': 'MomentGuard deterministic decision', 'status': 'local'},
                {'label': 'IBM watsonx.ai / Granite', 'status': 'verified'},
                {'label': latest.get('tool') or 'Granite explanation', 'status': 'verified'},
                {'label': 'Safety authority remained deterministic', 'status': 'local'},
            ],
        }
    return {
        'verified': False,
        'status': 'IBM adapter ready · runtime execution not yet verified',
        'provider': None,
        'latencyMs': None,
        'trace': traces[-1] if traces else None,
        'steps': [
            {'label': 'MomentGuard deterministic coordinator', 'status': 'local'},
            {'label': 'Game Intelligence calculation', 'status': 'local'},
            {'label': 'Venue routing and queue tools', 'status': 'local'},
            {'label': 'IBM watsonx.ai / Granite explanation', 'status': 'unverified'},
            {'label': 'Recommendation safety validation', 'status': 'local'},
        ],
        'note': 'No successful watsonx runtime trace is present yet. Configure backend/.env, then use the Proof Center button to run a real IBM Granite explanation. Local fallback is never mislabeled as IBM execution.',
    }


def build_proof(runtime):
    rec = runtime.recommendation()
    fan = runtime.fan
    game = runtime.game
    selected = rec.get('destination')
    selected_name = rec.get('calculation', {}).get('name') if rec.get('calculation') else None

    evaluated = []
    for option in rec.get('options', []):
        is_selected = option['destination'] == selected and rec['recommendedMode'] == 'trip'
        if is_selected:
            reason = 'Selected as the fastest eligible full round trip that satisfies the active decision policy.'
        elif option['roundTripMinutes'] > rec['availableWindowMinutes']:
            reason = f"Rejected: {option['roundTripMinutes']:.2f} min trip exceeds the {rec['availableWindowMinutes']:.2f} min available window."
        elif rec['riskScore'] >= runtime.settings.risk_threshold:
            reason = f"Rejected for departure: Moment Risk {rec['riskScore']} is above the {runtime.settings.risk_threshold} safety threshold."
        elif selected_name:
            delta = option['roundTripMinutes'] - rec['calculation']['roundTripMinutes']
            reason = f"Not selected: {max(0, delta):.2f} min slower than {selected_name}."
        else:
            reason = 'Eligible route, but current policy safely deferred the trip.'
        evaluated.append({**option, 'selected': is_selected, 'decision': 'SELECTED' if is_selected else 'REJECTED', 'why': reason})

    delivery = rec.get('bestAlternative')
    if delivery:
        evaluated.append({
            'destination': 'seat-delivery',
            'name': 'Seat delivery',
            'roundTripMinutes': delivery['estimatedMinutes'],
            'selected': rec['recommendedMode'] == 'delivery',
            'decision': 'SELECTED' if rec['recommendedMode'] == 'delivery' else 'ALTERNATIVE',
            'why': 'Keeps the fan seated while the game state or available window makes a concourse trip higher risk.',
            'delivery': True,
        })

    accessibility = []
    for facility in runtime.facilities:
        if facility['need'] != fan.need:
            continue
        route_result = route(runtime.graph, fan.position, facility['node'], fan)
        eligible = facility['open'] and (not fan.accessible or facility['accessible']) and route_result is not None
        if not facility['open']:
            why = 'Rejected because the facility is closed.'
        elif fan.accessible and not facility['accessible']:
            why = 'Rejected because the facility is not marked accessible.'
        elif route_result is None:
            why = 'Rejected because no eligible route exists for the active accessibility profile.'
        else:
            why = 'Eligible under the active accessibility profile.'
        accessibility.append({
            'facility': facility['id'], 'name': facility['name'], 'eligible': eligible,
            'facilityAccessible': facility['accessible'], 'route': route_result, 'why': why,
        })

    margin = rec.get('safeWindow', {}).get('marginMinutes')
    if rec['action'] in {'STAY', 'RETURN'} and rec['riskScore'] >= runtime.settings.risk_threshold:
        assurance = 'HIGH'
        assurance_reason = 'The high-risk rule is supported by multiple explicit game-state signals.'
    elif rec['action'] == 'GO' and margin is not None and margin >= runtime.settings.safety_buffer_minutes:
        assurance = 'HIGH'
        assurance_reason = 'The full route, queue, service, return path and configured safety buffer fit with additional margin.'
    elif rec['action'] == 'GO':
        assurance = 'MEDIUM'
        assurance_reason = 'The trip fits, but the remaining margin is narrow; MomentGuard continues monitoring for changes.'
    else:
        assurance = 'CONSERVATIVE'
        assurance_reason = 'When evidence does not support a safe departure, MomentGuard defers instead of manufacturing a GO recommendation.'

    return {
        'label': 'LIVE DECISION EVIDENCE',
        'game': {
            'score': f"{game['scoreA']}–{game['scoreB']}",
            'quarter': game['quarter'],
            'clockSeconds': game['clockSeconds'],
            'paused': game['paused'],
            'scenario': game['scenario'],
            'availableWindowMinutes': game['availableWindowMinutes'],
            'possession': game.get('possession'),
            'significantEvent': game.get('significantEvent'),
        },
        'request': {'need': fan.need, 'accessible': fan.accessible, 'seatDelivery': fan.delivery, 'seat': fan.seat},
        'risk': {'score': rec['riskScore'], 'scale': rec['riskScale'], 'breakdown': rec['riskBreakdown']},
        'options': evaluated,
        'finalDecision': {
            'action': rec['action'], 'destination': rec['destination'], 'mode': rec['recommendedMode'],
            'title': rec['title'], 'reason': rec['reason'], 'explanation': rec['explanation'],
            'safeWindow': rec['safeWindow'], 'assurance': assurance, 'assuranceReason': assurance_reason,
        },
        'whyNotLeaveNow': rec['reason'] if rec['action'] != 'GO' else None,
        'accessibility': {
            'enabled': fan.accessible,
            'checks': accessibility,
        },
        'ibmExecution': _ibm_execution(runtime),
        'provenance': {
            'game': 'Simulated MomentGuard seed',
            'venue': 'Fictional Northstar Arena',
            'decisionAuthority': 'Deterministic MomentGuard safety engine',
        },
    }
