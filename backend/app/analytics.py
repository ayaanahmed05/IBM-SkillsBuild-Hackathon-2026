"""Small deterministic cohort experiment, with all reported metrics reduced from events."""
import random
from .engine import seed_venue, options, recommend
from .models import Fan

def assignments(fans, game, facilities, graph):
    counts={}
    results=[]
    for fan in sorted(fans,key=lambda f:f.id):
        choices=options(game,facilities,graph,fan,assigned=counts)
        if not choices or recommend(game,facilities,graph,fan)['action']!='GO':
            results.append({'fan':fan.id,'destination':None,'action':'WAIT'})
            continue
        choice=choices[0]
        if choice['roundTripMinutes']>game['availableWindowMinutes']:
            results.append({'fan':fan.id,'destination':None,'action':'WAIT'})
            continue
        counts[choice['destination']]=counts.get(choice['destination'],0)+1
        results.append({'fan':fan.id,'action':'GO',**choice})
    return results

def summarize(events):
    rows=[e['payload']['details'] for e in events if e['type']=='trip_measurement']
    return dict(label='Simulated; measured event totals',tripSeconds=round(sum(r['seconds'] for r in rows),3),queueSeconds=round(sum(r['seconds'] for r in rows if r['phase']=='queuing'),3),importantMomentExposureSeconds=round(sum(r['seconds'] for r in rows if r['importantMomentMissed']),3),routeChanges=sum(e['type']=='route_update' for e in events),walkingMeters=round(sum(r.get('walkingMeters',0) for r in rows),3),agentErrors=sum(not e['payload']['details']['trace']['success'] for e in events if e['type']=='agent_action'),eventCount=len(events))

def experiment(seed=42, count=30):
    rng=random.Random(seed)
    facilities,graph=seed_venue()
    fans=[Fan(id=f'{i:03}',need=rng.choice(['food','restroom','shop']),accessible=rng.random()<0.2,seat=rng.choice(['seat-101','seat-102'])) for i in range(count)]
    for fan in fans:
        fan.position=fan.seat
    game={'momentIntensity':28,'paused':True,'availableWindowMinutes':8}
    runs={}
    for policy in ['baseline','momentguard','crowdflow']:
        events=[]; counts={}
        distributed=assignments(fans,game,facilities,graph) if policy=='crowdflow' else None
        for i,fan in enumerate(fans):
            choices=options(game,facilities,graph,fan,assigned=counts)
            if distributed is not None:
                assigned=distributed[i]
                choice=assigned if assigned['destination'] else None
            else:
                choice=(min(choices,key=lambda c:c['route']['distanceMeters']) if policy=='baseline' else choices[0]) if choices else None
                if policy=='momentguard' and choice and choice['roundTripMinutes']>8:
                    choice=None
            if choice:
                counts[choice['destination']]=counts.get(choice['destination'],0)+1
                duration=choice['roundTripMinutes']-choice['safetyBufferMinutes']
                events.append(dict(type='trip_completed',fan=fan.id,destination=choice['destination'],queueMinutes=choice['queueMinutes'],tripMinutes=duration,walkingMeters=choice['route']['distanceMeters']+choice['returnRoute']['distanceMeters'],importantMomentExposureMinutes=max(0,duration-8),safetyViolation=choice['roundTripMinutes']>8))
        runs[policy]=dict(events=events,metrics=dict(trips=len(events),queueMinutes=round(sum(e['queueMinutes'] for e in events),3),tripMinutes=round(sum(e['tripMinutes'] for e in events),3),walkingMeters=sum(e['walkingMeters'] for e in events),importantMomentExposureMinutes=round(sum(e['importantMomentExposureMinutes'] for e in events),3),safetyViolations=sum(e['safetyViolation'] for e in events),facilityUtilization=counts))
    return dict(seed=seed,fans=count,label='SIMULATED cohort estimate; one departure wave; baseline chooses nearest; deferred trips excluded',runs=runs)

if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=42);parser.add_argument('--fans',type=int,default=30)
    args=parser.parse_args();print(json.dumps(experiment(args.seed,args.fans),indent=2))
