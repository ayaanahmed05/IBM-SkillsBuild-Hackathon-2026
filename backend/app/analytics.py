"""Deterministic cohort experiments and event-derived analytics.

The experiment is intentionally transparent: all reported results can be reproduced
from one seed and the underlying simulated trip records are returned with the metrics.
"""
import math
import random
from statistics import pvariance
from .engine import seed_venue, options, recommend
from .models import Fan


def assignments(fans, game, facilities, graph):
    """CrowdFlow: sequentially reserve predicted demand so later fans see future load."""
    counts = {}
    results = []
    for fan in sorted(fans, key=lambda f: f.id):
        base = recommend(game, facilities, graph, fan)
        choices = options(game, facilities, graph, fan, assigned=counts)
        if base['action'] != 'GO' or not choices:
            results.append({'fan': fan.id, 'destination': None, 'action': 'WAIT'})
            continue
        eligible = [choice for choice in choices if choice['roundTripMinutes'] <= game['availableWindowMinutes']]
        if not eligible:
            results.append({'fan': fan.id, 'destination': None, 'action': 'WAIT'})
            continue
        choice = eligible[0]
        counts[choice['destination']] = counts.get(choice['destination'], 0) + 1
        results.append({'fan': fan.id, 'action': 'GO', **choice})
    return results


def summarize(events):
    rows = [e['payload']['details'] for e in events if e['type'] == 'trip_measurement']
    return dict(
        label='Simulated; measured event totals',
        tripSeconds=round(sum(r['seconds'] for r in rows), 3),
        queueSeconds=round(sum(r['seconds'] for r in rows if r['phase'] == 'queuing'), 3),
        importantMomentExposureSeconds=round(sum(r['seconds'] for r in rows if r['importantMomentMissed']), 3),
        routeChanges=sum(e['type'] == 'route_update' for e in events),
        walkingMeters=round(sum(r.get('walkingMeters', 0) for r in rows), 3),
        agentErrors=sum(not e['payload']['details']['trace']['success'] for e in events if e['type'] == 'agent_action'),
        eventCount=len(events),
    )


def _metrics(events, counts, requests):
    trips = len(events)
    queue = sum(e['queueMinutes'] for e in events)
    trip_minutes = sum(e['tripMinutes'] for e in events)
    exposure = sum(e['importantMomentExposureMinutes'] for e in events)
    violations = sum(e['safetyViolation'] for e in events)
    loads = list(counts.values())
    total_load = sum(loads)
    return dict(
        requests=requests,
        trips=trips,
        safeRequestsServed=sum(not e['safetyViolation'] for e in events),
        queueMinutes=round(queue, 3),
        averageQueueMinutes=round(queue / trips, 3) if trips else 0,
        tripMinutes=round(trip_minutes, 3),
        averageTripMinutes=round(trip_minutes / trips, 3) if trips else 0,
        walkingMeters=sum(e['walkingMeters'] for e in events),
        importantMomentExposureMinutes=round(exposure, 3),
        highRiskExposurePerTrip=round(exposure / trips, 3) if trips else 0,
        safetyViolations=violations,
        unsafeDepartureRate=round(violations / trips, 4) if trips else 0,
        facilityUtilization=counts,
        facilityLoadVariance=round(pvariance(loads), 3) if len(loads) > 1 else 0,
        maxFacilityShare=round(max(loads) / total_load, 4) if total_load else 0,
    )


def _event(fan, choice, available):
    duration = choice['roundTripMinutes'] - choice['safetyBufferMinutes']
    return dict(
        type='trip_completed',
        fan=fan.id,
        destination=choice['destination'],
        queueMinutes=choice['queueMinutes'],
        tripMinutes=duration,
        walkingMeters=choice['route']['distanceMeters'] + choice['returnRoute']['distanceMeters'],
        importantMomentExposureMinutes=max(0, duration - available),
        safetyViolation=choice['roundTripMinutes'] > available,
    )


def _build_fans(seed, count):
    rng = random.Random(seed)
    fans = [
        Fan(
            id=f'{i:03}',
            need=rng.choices(['food', 'restroom', 'shop'], weights=[0.62, 0.28, 0.10])[0],
            accessible=rng.random() < 0.16,
            seat=rng.choice(['seat-101', 'seat-102']),
        )
        for i in range(count)
    ]
    for fan in fans:
        fan.position = fan.seat
    return fans


def _run_baseline(fans, game, facilities, graph):
    events, counts = [], {}
    for fan in fans:
        choices = options(game, facilities, graph, fan, assigned={})
        if not choices:
            continue
        choice = min(choices, key=lambda c: (c['route']['distanceMeters'], c['destination']))
        counts[choice['destination']] = counts.get(choice['destination'], 0) + 1
        events.append(_event(fan, choice, game['availableWindowMinutes']))
    return dict(events=events, metrics=_metrics(events, counts, len(fans)))


def _run_momentguard(fans, game, facilities, graph):
    events, counts = [], {}
    for fan in fans:
        rec = recommend(game, facilities, graph, fan)
        choice = rec['calculation'] if rec['action'] == 'GO' else None
        if not choice:
            continue
        counts[choice['destination']] = counts.get(choice['destination'], 0) + 1
        events.append(_event(fan, choice, game['availableWindowMinutes']))
    return dict(events=events, metrics=_metrics(events, counts, len(fans)))


def _run_crowdflow(fans, game, facilities, graph):
    events, counts = [], {}
    fan_by_id = {fan.id: fan for fan in fans}
    for assigned in assignments(fans, game, facilities, graph):
        if not assigned.get('destination'):
            continue
        fan = fan_by_id[assigned['fan']]
        counts[assigned['destination']] = counts.get(assigned['destination'], 0) + 1
        events.append(_event(fan, assigned, game['availableWindowMinutes']))
    return dict(events=events, metrics=_metrics(events, counts, len(fans)))


def _food_peak_share(run):
    counts = run['metrics']['facilityUtilization']
    food = [counts.get('food-north', 0), counts.get('food-south', 0)]
    total = sum(food)
    return max(food) / total if total else 0


def experiment(seed=42, count=30):
    """Two transparent simulated waves: safety and crowd-distribution.

    The safety wave asks whether a fan should leave during a tight pause. The crowd
    wave uses a longer pause so CrowdFlow can demonstrate demand-aware distribution.
    """
    facilities, graph = seed_venue()
    fans = _build_fans(seed, count)
    common = dict(
        scenario='timeout', scoreA=106, scoreB=105, clockSeconds=92, quarter=4,
        momentIntensity=28, paused=True, possession='HOME', significantEvent=None,
    )

    safety_game = {**common, 'availableWindowMinutes': 4.5}
    crowd_game = {**common, 'availableWindowMinutes': 9.0}

    safety_runs = {
        'baseline': _run_baseline(fans, safety_game, facilities, graph),
        'momentguard': _run_momentguard(fans, safety_game, facilities, graph),
        'crowdflow': _run_crowdflow(fans, safety_game, facilities, graph),
    }
    crowd_runs = {
        'baseline': _run_baseline(fans, crowd_game, facilities, graph),
        'momentguard': _run_momentguard(fans, crowd_game, facilities, graph),
        'crowdflow': _run_crowdflow(fans, crowd_game, facilities, graph),
    }

    baseline_safe = safety_runs['baseline']['metrics']
    moment_safe = safety_runs['momentguard']['metrics']
    mg_peak = _food_peak_share(crowd_runs['momentguard'])
    cf_peak = _food_peak_share(crowd_runs['crowdflow'])

    scorecard = {
        'unsafeDeparturesAvoided': max(0, baseline_safe['safetyViolations'] - moment_safe['safetyViolations']),
        'highRiskMinutesAvoided': round(max(0, baseline_safe['importantMomentExposureMinutes'] - moment_safe['importantMomentExposureMinutes']), 2),
        'crowdPeakConcentrationBeforePct': round(mg_peak * 100, 1),
        'crowdPeakConcentrationAfterPct': round(cf_peak * 100, 1),
        'crowdPeakConcentrationReductionPct': round(max(0, mg_peak - cf_peak) * 100, 1),
        'label': 'SIMULATED POC RESULTS — not a real-world performance claim',
    }

    return dict(
        seed=seed,
        fans=count,
        label='SIMULATED two-wave cohort; identical fans and venue state across policies; underlying records included',
        methodology={
            'safetyWave': '4.5-minute pause tests whether the system prevents trips that cannot safely return.',
            'crowdWave': '9-minute pause tests whether demand-aware assignment spreads food traffic across concessions.',
            'baseline': 'Nearest eligible facility; no safe-window or group-demand awareness.',
            'momentguard': 'Independent safe-window decision using complete round-trip estimate.',
            'crowdflow': 'MomentGuard safety plus predicted group-demand reservations and load-aware assignment.',
        },
        scorecard=scorecard,
        # Keep runs as the safety wave for API/backwards-compatibility and test auditability.
        runs=safety_runs,
        waves={'safety': safety_runs, 'crowd': crowd_runs},
    )


if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--fans', type=int, default=30)
    args = parser.parse_args()
    print(json.dumps(experiment(args.seed, args.fans), indent=2))
