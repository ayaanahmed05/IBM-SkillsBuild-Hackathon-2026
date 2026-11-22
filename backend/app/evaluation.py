"""Reproducible MomentGuard evaluation suite used by Judge Mode.

This is a deterministic POC validation harness, not a claim of real-world clinical,
safety, or stadium performance. Every result is recomputed from the same decision
engine used by the application.
"""
from copy import deepcopy
from .engine import seed_venue, recommend
from .models import Fan


def _game(**overrides):
    base = dict(
        scenario='timeout', scoreA=106, scoreB=105, clockSeconds=92, quarter=4,
        momentIntensity=28, availableWindowMinutes=8.0, paused=True,
        possession='HOME', significantEvent=None, gameState='PLAY PAUSED',
    )
    base.update(overrides)
    return base


def _record(category, case_id, passed, expectation, observed, details=None):
    return {
        'category': category,
        'id': case_id,
        'passed': bool(passed),
        'expectation': expectation,
        'observed': observed,
        'details': details or {},
    }


def _run_high_risk():
    results = []
    facilities, graph = seed_venue()
    for i in range(30):
        margin = i % 3
        seconds = 35 + (i % 6) * 12
        game = _game(
            scenario='critical', scoreA=100 + margin, scoreB=100,
            clockSeconds=seconds, availableWindowMinutes=0, paused=False,
            significantEvent='Decisive possession', gameState='CLOSE GAME',
        )
        fan = Fan(need=['food', 'restroom', 'shop'][i % 3])
        rec = recommend(game, deepcopy(facilities), graph.copy(), fan)
        passed = rec['action'] == 'STAY' and rec['riskScore'] >= 75
        results.append(_record(
            'highRisk', f'HR-{i+1:02}', passed,
            'STAY with Moment Risk ≥ 75', f"{rec['action']} · risk {rec['riskScore']}",
            {'riskScore': rec['riskScore'], 'riskBreakdown': rec['riskBreakdown']},
        ))
    return results


def _run_safe_windows():
    results = []
    facilities, graph = seed_venue()
    for i in range(30):
        # Restroom has the shortest eligible round trip and makes a stable safe-window test.
        window = 5.5 + (i % 6) * 0.5
        game = _game(scoreA=90 + (i % 4), scoreB=85, clockSeconds=180 + i, availableWindowMinutes=window, paused=True)
        fan = Fan(need='restroom', speed=65 + (i % 5) * 4)
        rec = recommend(game, deepcopy(facilities), graph.copy(), fan)
        passed = rec['action'] == 'GO' and rec['safeWindow']['fits'] and rec['safeWindow']['marginMinutes'] >= 0
        results.append(_record(
            'safeWindow', f'SW-{i+1:02}', passed,
            'GO only when full round trip + safety buffer fits',
            f"{rec['action']} · margin {rec['safeWindow']['marginMinutes']}",
            {'safeWindow': rec['safeWindow'], 'destination': rec['destination']},
        ))
    return results


def _run_queue_spikes():
    results = []
    for i in range(20):
        facilities, graph = seed_venue()
        game = _game(scoreA=88, scoreB=82, clockSeconds=240, availableWindowMinutes=12, paused=True)
        fan = Fan(need='food', speed=72)
        before = recommend(game, deepcopy(facilities), graph.copy(), fan)
        # Spike whichever food option is currently preferred so a robust system must replan.
        spiked_id = before['destination']
        for facility in facilities:
            if facility['id'] == spiked_id:
                facility['queue'] = 20 + i
                facility['congestion'] = 1.5
        after = recommend(game, facilities, graph, fan)
        passed = after['destination'] != spiked_id or after['action'] in {'WAIT', 'STAY'} or after['recommendedMode'] == 'delivery'
        results.append(_record(
            'queueSpike', f'QS-{i+1:02}', passed,
            'Replan away from a severely spiked destination or safely defer',
            f"{spiked_id} → {after['destination'] or after['action']}",
            {'before': before['destination'], 'after': after['destination'], 'action': after['action']},
        ))
    return results


def _run_accessibility():
    results = []
    for i in range(10):
        facilities, graph = seed_venue()
        game = _game(scoreA=82, scoreB=74, clockSeconds=378, quarter=3, availableWindowMinutes=10, paused=True, gameState='INTERMISSION')
        fan = Fan(need='shop', accessible=True, speed=60 + i)
        rec = recommend(game, facilities, graph, fan)
        passed = rec['action'] == 'WAIT' and rec['destination'] is None and not rec['options']
        results.append(_record(
            'accessibility', f'AC-{i+1:02}', passed,
            'Reject inaccessible shop and route; do not invent an alternative',
            f"{rec['action']} · destination {rec['destination']}",
            {'accessible': True, 'eligibleOptions': len(rec['options'])},
        ))
    return results


def _run_closures():
    results = []
    for i in range(10):
        facilities, graph = seed_venue()
        game = _game(scoreA=82, scoreB=74, clockSeconds=378, quarter=3, availableWindowMinutes=12, paused=True, gameState='INTERMISSION')
        fan = Fan(need='food', delivery=False)
        before = recommend(game, deepcopy(facilities), graph.copy(), fan)
        chosen = before['destination']
        for facility in facilities:
            if facility['id'] == chosen:
                facility['open'] = False
        after = recommend(game, facilities, graph, fan)
        passed = after['destination'] != chosen and all(opt['destination'] != chosen for opt in after['options'])
        results.append(_record(
            'facilityClosure', f'FC-{i+1:02}', passed,
            'Closed facility must be removed and recommendation must replan',
            f"{chosen} closed → {after['destination'] or after['action']}",
            {'closed': chosen, 'after': after['destination'], 'action': after['action']},
        ))
    return results


def evaluation_suite():
    cases = _run_high_risk() + _run_safe_windows() + _run_queue_spikes() + _run_accessibility() + _run_closures()
    names = {
        'highRisk': 'High-risk game situations',
        'safeWindow': 'Safe departure windows',
        'queueSpike': 'Queue disruptions',
        'accessibility': 'Accessible routing',
        'facilityClosure': 'Facility closures',
    }
    categories = []
    for key in names:
        rows = [row for row in cases if row['category'] == key]
        categories.append({
            'id': key,
            'label': names[key],
            'passed': sum(row['passed'] for row in rows),
            'total': len(rows),
        })
    failed = [row for row in cases if not row['passed']]
    passed = sum(row['passed'] for row in cases)
    return {
        'label': 'REPRODUCIBLE POC EVALUATION — deterministic simulated scenarios, not a real-world performance claim',
        'total': len(cases),
        'passed': passed,
        'failed': len(cases) - passed,
        'passRatePct': round(passed / len(cases) * 100, 1) if cases else 0,
        'safetyViolationsDetected': sum(
            row['category'] == 'highRisk' and not row['passed'] for row in cases
        ),
        'categories': categories,
        'failures': failed[:20],
        'methodology': {
            'highRisk': '30 close, late, live-play states must produce STAY and a high explainable risk score.',
            'safeWindow': '30 paused-play states validate complete round-trip fit including the safety buffer.',
            'queueSpike': '20 severe queue disruptions must trigger replanning, deferral, or a lower-risk fulfillment mode.',
            'accessibility': '10 wheelchair-accessible profiles must reject the intentionally inaccessible fan-shop route.',
            'facilityClosure': '10 closures verify that a closed recommendation is removed before replanning.',
        },
        'cases': cases,
    }
