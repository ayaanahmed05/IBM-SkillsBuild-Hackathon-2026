"""Pure deterministic calculations. Scores are heuristic, never probabilities."""
import networkx as nx
from .models import Fan

CATALOG = [{'id': 'water', 'name': 'Water', 'priceCents': 300, 'serviceMinutes': 0.5},
           {'id': 'snack', 'name': 'Snack box', 'priceCents': 800, 'serviceMinutes': 1}]

def seed_venue():
    facilities = [
        dict(id='food-north', node='north', need='food', name='North Concessions', queue=4, capacity=2, service=1, accessible=True, delivery=True, open=True, congestion=1.0),
        dict(id='food-south', node='south', need='food', name='South Concessions', queue=1, capacity=2, service=1, accessible=True, delivery=False, open=True, congestion=1.0),
        dict(id='wc-north', node='north', need='restroom', name='Accessible Restroom', queue=0, capacity=3, service=0.5, accessible=True, delivery=False, open=True, congestion=1.0),
        dict(id='shop-east', node='east', need='shop', name='Fan Shop', queue=2, capacity=1, service=1, accessible=False, delivery=False, open=True, congestion=1.0)]
    graph = nx.Graph()
    for a, b, metres, accessible in [('seat-101','junction',25,True),('seat-102','junction',40,True),('junction','north',35,True),('junction','south',90,True),('junction','east',50,False),('south','east',80,True),('north','south',110,True)]:
        graph.add_edge(a,b,metres=metres,accessible=accessible,open=True,congestion=1.0)
    return facilities, graph

def route(graph, source, target, fan):
    eligible = nx.subgraph_view(graph, filter_edge=lambda a,b: graph[a][b]['open'] and (not fan.accessible or graph[a][b]['accessible']))
    def weight(a,b,d):
        return d['metres'] * d['congestion']
    try:
        path = nx.shortest_path(eligible, source, target, weight=weight)
        edges = [graph[a][b] for a,b in zip(path,path[1:])]
        return dict(path=path, distanceMeters=sum(e['metres'] for e in edges), minutes=round(sum(weight(None,None,e) for e in edges)/fan.speed,3))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

def options(game, facilities, graph, fan, buffer=0.5, assigned=None):
    result=[]
    for f in facilities:
        if f['need'] != fan.need or not f['open'] or (fan.accessible and not f['accessible']):
            continue
        outward=route(graph,fan.position,f['node'],fan)
        home=route(graph,f['node'],fan.seat,fan)
        if outward is None or home is None:
            continue
        queue=(f['queue']+(assigned or {}).get(f['id'],0))/f['capacity']*f['service']*f['congestion']
        total=outward['minutes']+queue+f['service']+home['minutes']+buffer
        result.append(dict(destination=f['id'],name=f['name'],route=outward,returnRoute=home,queueMinutes=round(queue,3),serviceMinutes=f['service'],safetyBufferMinutes=buffer,roundTripMinutes=round(total,3)))
    return sorted(result,key=lambda x:(x['roundTripMinutes'],x['destination']))

def risk(game):
    return game['momentIntensity']

def recommend(game, facilities, graph, fan, threshold=75, buffer=0.5):
    choices=options(game, facilities, graph, fan, buffer)
    best=choices[0] if choices else None
    away=fan.position != fan.seat or (fan.trip is not None and fan.trip['status'] not in ['completed','at_seat'])
    if away and (not game['paused'] or risk(game)>=threshold):
        action,reason='RETURN','Play is active or a significant moment is underway. Return to your seat.'
    elif risk(game)>=threshold:
        action,reason='STAY','A significant game moment is underway.'
    elif not best:
        action,reason='WAIT','No open facility with an eligible route meets your preferences.'
    elif away:
        action,reason='WAIT','Trip is in progress; monitor the remaining pause.'
    elif best['roundTripMinutes']<=game['availableWindowMinutes']:
        action,reason='GO','The complete trip including service and safety buffer fits the available window.'
    else:
        action,reason='WAIT','The complete trip exceeds the available window.'
    trip=dict(walkMinutes=best['route']['minutes'],queueMinutes=best['queueMinutes'],distanceMeters=best['route']['distanceMeters']) if best else dict(walkMinutes=0,queueMinutes=0,distanceMeters=0)
    return dict(action=action,confidence=None,title={'GO':'A suitable trip is available','WAIT':'Wait for a safer window','STAY':'Stay for the big moment','RETURN':'Return to your seat now'}[action],explanation=reason,reason=reason,roundTripMinutes=best['roundTripMinutes'] if best else None,tripEstimate=trip,destination=best['destination'] if best else None,options=choices,calculation=best,riskScore=risk(game),riskScale='heuristic 0–100',availableWindowMinutes=game['availableWindowMinutes'],metrics=dict(queueMinutesAvoided=0,walkingMetersReduced=0,momentsProtected=0))
