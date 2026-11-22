"""Deterministic MomentGuard calculations.

The core decision engine intentionally remains explainable and auditable. Scores are
heuristics, never probabilities. IBM/LLM layers may explain or orchestrate a decision,
but this module is the safety authority for the demo.
"""
import networkx as nx

CATALOG = [
    {'id': 'water', 'name': 'Water', 'priceCents': 300, 'serviceMinutes': 0.5},
    {'id': 'snack', 'name': 'Snack box', 'priceCents': 800, 'serviceMinutes': 1},
    {'id': 'burger', 'name': 'Arena burger combo', 'priceCents': 1450, 'serviceMinutes': 1.5},
    {'id': 'popcorn', 'name': 'Popcorn', 'priceCents': 650, 'serviceMinutes': 0.75},
]


def seed_venue():
    facilities = [
        dict(id='food-north', node='north', need='food', name='North Market', queue=4, capacity=2, service=1, accessible=True, delivery=True, open=True, congestion=1.0),
        dict(id='food-south', node='south', need='food', name='South Market', queue=1, capacity=2, service=1, accessible=True, delivery=False, open=True, congestion=1.0),
        dict(id='wc-north', node='north', need='restroom', name='Accessible Restroom', queue=0, capacity=3, service=0.5, accessible=True, delivery=False, open=True, congestion=1.0),
        dict(id='shop-east', node='east', need='shop', name='Fan Shop', queue=2, capacity=1, service=1, accessible=False, delivery=False, open=True, congestion=1.0),
    ]
    graph = nx.Graph()
    for a, b, metres, accessible in [
        ('seat-101', 'junction', 25, True),
        ('seat-102', 'junction', 40, True),
        ('junction', 'north', 35, True),
        ('junction', 'south', 90, True),
        ('junction', 'east', 50, False),
        ('south', 'east', 80, True),
        ('north', 'south', 110, True),
    ]:
        graph.add_edge(a, b, metres=metres, accessible=accessible, open=True, congestion=1.0)
    return facilities, graph


def route(graph, source, target, fan):
    eligible = nx.subgraph_view(
        graph,
        filter_edge=lambda a, b: graph[a][b]['open'] and (not fan.accessible or graph[a][b]['accessible']),
    )

    def weight(a, b, d):
        return d['metres'] * d['congestion']

    try:
        path = nx.shortest_path(eligible, source, target, weight=weight)
        edges = [graph[a][b] for a, b in zip(path, path[1:])]
        return dict(
            path=path,
            distanceMeters=sum(e['metres'] for e in edges),
            minutes=round(sum(weight(None, None, e) for e in edges) / fan.speed, 3),
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def options(game, facilities, graph, fan, buffer=0.5, assigned=None):
    """Return complete eligible round-trip plans ordered by estimated total time."""
    result = []
    for facility in facilities:
        if facility['need'] != fan.need or not facility['open'] or (fan.accessible and not facility['accessible']):
            continue
        outward = route(graph, fan.position, facility['node'], fan)
        home = route(graph, facility['node'], fan.seat, fan)
        if outward is None or home is None:
            continue
        predicted_people = facility['queue'] + (assigned or {}).get(facility['id'], 0)
        queue = predicted_people / facility['capacity'] * facility['service'] * facility['congestion']
        total = outward['minutes'] + queue + facility['service'] + home['minutes'] + buffer
        result.append(
            dict(
                destination=facility['id'],
                name=facility['name'],
                route=outward,
                returnRoute=home,
                queueMinutes=round(queue, 3),
                serviceMinutes=facility['service'],
                safetyBufferMinutes=buffer,
                roundTripMinutes=round(total, 3),
                accessible=facility['accessible'],
                delivery=facility['delivery'],
                predictedPeople=predicted_people,
            )
        )
    return sorted(result, key=lambda x: (x['roundTripMinutes'], x['destination']))


def risk_breakdown(game):
    """Explainably derive a 0-100 moment-risk heuristic from game state."""
    entries = []

    def add(label, points, detail):
        entries.append({'label': label, 'points': points, 'detail': detail})

    diff = abs(int(game.get('scoreA', 0)) - int(game.get('scoreB', 0)))
    if diff <= 2:
        add('One-possession score', 25, f'{diff}-point margin')
    elif diff <= 5:
        add('Close score', 18, f'{diff}-point margin')
    elif diff <= 10:
        add('Competitive score', 8, f'{diff}-point margin')

    quarter = int(game.get('quarter', 1))
    seconds = float(game.get('clockSeconds', 720))
    if quarter >= 4 and seconds <= 120:
        add('Final two minutes', 30, f'{int(seconds)} seconds remaining')
    elif quarter >= 4 and seconds <= 300:
        add('Late fourth quarter', 20, f'{int(seconds // 60)}:{int(seconds % 60):02d} remaining')
    elif quarter >= 3:
        add('Late-game context', 5, f'Quarter {quarter}')

    if game.get('paused'):
        add('Play paused', -45, 'Timeout/intermission creates a safer movement window')
    else:
        add('Live play', 15, 'Play is active')

    if game.get('significantEvent'):
        add('Significant event', 20, str(game['significantEvent']))

    if game.get('scenario') == 'resumed':
        add('Play just resumed', 10, 'Window closed earlier than the fan trip plan')

    if game.get('possession'):
        add('Possession active', 5, f"{game['possession']} possession")

    total = max(0, min(100, sum(item['points'] for item in entries)))
    return total, entries


def risk(game):
    return risk_breakdown(game)[0]


def delivery_option(facilities, fan):
    if fan.need != 'food' or not fan.delivery:
        return None
    eligible = [
        f for f in facilities
        if f['need'] == 'food' and f['open'] and f['delivery'] and (not fan.accessible or f['accessible'])
    ]
    if not eligible:
        return None
    facility = min(eligible, key=lambda f: (f['queue'] / f['capacity']) * f['service'] * f['congestion'])
    prep = 2.0 + (facility['queue'] / facility['capacity']) * facility['service'] * facility['congestion']
    return {
        'type': 'delivery',
        'facility': facility['id'],
        'name': facility['name'],
        'estimatedMinutes': round(prep, 1),
        'title': 'Deliver food to your seat',
        'reason': 'Protect the moment without making a concourse trip.',
    }


def recommend(game, facilities, graph, fan, threshold=75, buffer=0.5):
    choices = options(game, facilities, graph, fan, buffer)
    best = choices[0] if choices else None
    score, breakdown = risk_breakdown(game)
    delivery = delivery_option(facilities, fan)
    away = fan.position != fan.seat or (fan.trip is not None and fan.trip['status'] not in ['completed', 'at_seat'])

    if away and (not game['paused'] or score >= threshold):
        action, reason = 'RETURN', 'Play is active or a high-value moment is underway. Return to your seat now.'
    elif score >= threshold:
        action, reason = 'STAY', 'The current game state is too important to recommend leaving your seat.'
    elif not best:
        action, reason = 'WAIT', 'No open facility with an eligible route currently matches your preferences.'
    elif away:
        action, reason = 'WAIT', 'Your trip is already in progress. MomentGuard is monitoring the remaining window.'
    elif best['roundTripMinutes'] <= game['availableWindowMinutes']:
        action, reason = 'GO', 'The complete trip, including return travel and a safety buffer, fits inside the current window.'
    else:
        action, reason = 'WAIT', 'The best available round trip does not fit inside the current safe window.'

    if delivery and action in {'STAY', 'WAIT'} and not away:
        explanation = f"{reason} Seat delivery is available from {delivery['name']} as a lower-risk alternative."
        recommended_mode = 'delivery'
    else:
        explanation = reason
        recommended_mode = 'trip' if action == 'GO' else 'none'

    trip = (
        dict(
            walkMinutes=best['route']['minutes'],
            queueMinutes=best['queueMinutes'],
            distanceMeters=best['route']['distanceMeters'],
        )
        if best
        else dict(walkMinutes=0, queueMinutes=0, distanceMeters=0)
    )

    required = best['roundTripMinutes'] if best else None
    available = round(float(game['availableWindowMinutes']), 3)
    margin = round(available - required, 3) if required is not None else None

    title = {
        'GO': 'Go now — your trip fits the safe window',
        'WAIT': 'Wait for a safer window',
        'STAY': 'Stay for what matters',
        'RETURN': 'Return to your seat now',
    }[action]

    if delivery and action in {'STAY', 'WAIT'} and not away:
        title = 'Stay seated — we found a safer alternative'

    return dict(
        action=action,
        confidence=None,
        title=title,
        explanation=explanation,
        reason=reason,
        roundTripMinutes=required,
        tripEstimate=trip,
        destination=best['destination'] if best else None,
        options=choices,
        calculation=best,
        riskScore=score,
        riskScale='explainable heuristic 0–100; not a probability',
        riskBreakdown=breakdown,
        availableWindowMinutes=available,
        safeWindow={
            'availableMinutes': available,
            'requiredMinutes': required,
            'marginMinutes': margin,
            'fits': bool(best and required <= available),
        },
        bestAlternative=delivery,
        recommendedMode=recommended_mode,
        metrics=dict(queueMinutesAvoided=0, walkingMetersReduced=0, momentsProtected=0),
    )
