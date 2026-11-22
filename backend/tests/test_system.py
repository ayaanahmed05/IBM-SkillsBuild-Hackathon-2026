import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from app.models import Fan
from app.agents import evaluate
from app.analytics import experiment

@pytest.fixture
def client():
    with TestClient(create_app(Settings(database_url='sqlite:///:memory:'))) as c:
        yield c

def post(c,path,body=None):
    response=c.post('/api/'+path,json=body or {})
    assert response.status_code==200,response.text
    return response.json()

def test_legacy_contract(client):
    assert client.get('/api/health').json()=={'ok':True,'service':'MomentGuard AI API','mode':'simulated-data'}
    s=client.get('/api/state').json()
    assert {'state','recommendation','updatedAt'}<=s.keys()
    assert {'scenario','trip','scoreA','scoreB','clock','gameState','momentIntensity','availableWindowMinutes'}<=s['state'].keys()
    assert {'action','confidence','title','explanation','reason','roundTripMinutes','tripEstimate','metrics'}<=s['recommendation'].keys()
    for path,body in [('scenario',{'scenario':'invalid'}),('need',{'need':'invalid'})]:
        assert client.post('/api/'+path,json=body).status_code==400
    for need in ['food','restroom','shop']:
        assert post(client,'need',{'need':need})['recommendation']['action']=='STAY'

def test_go_wait_return_and_seated_resumption(client):
    post(client,'scenario',{'scenario':'timeout'})
    assert post(client,'need',{'need':'restroom'})['recommendation']['action']=='GO'
    assert post(client,'need',{'need':'shop'})['recommendation']['action']=='WAIT'
    assert post(client,'scenario',{'scenario':'resumed'})['recommendation']['action']=='STAY'
    post(client,'scenario',{'scenario':'timeout'});post(client,'need',{'need':'restroom'});post(client,'trips/start')
    assert post(client,'scenario',{'scenario':'resumed'})['recommendation']['action']=='RETURN'
    done=post(client,'simulation/tick',{'seconds':600})
    assert done['fan']['position']==done['fan']['seat']
    assert done['recommendation']['action']!='RETURN'

def test_queue_closure_accessibility_routes(client):
    post(client,'scenario',{'scenario':'steady'})
    old=client.get('/api/state').json()['recommendation']['destination']
    changed=post(client,f'facilities/{old}',{'queue':100})
    assert changed['recommendation']['destination']!=old
    post(client,'facilities/food-north',{'open':False});post(client,'facilities/food-south',{'open':False})
    assert client.get('/api/state').json()['recommendation']['destination'] is None
    post(client,'need',{'need':'shop'})
    assert post(client,'preferences',{'accessible':True})['recommendation']['action']=='WAIT'
    post(client,'reset');post(client,'scenario',{'scenario':'steady'})
    post(client,'routes/junction/north',{'open':False})
    route=post(client,'need',{'need':'restroom'})['recommendation']['calculation']['route']['path']
    assert route==['seat-101','junction','south','north']

def test_orders_confirmation_delivery_and_cancel(client):
    body={'facility':'food-north','item':'water'}
    assert client.post('/api/orders',json=body).status_code==400
    o=post(client,'orders',{**body,'confirmed':True})
    assert o['simulated'] is True
    assert post(client,f"orders/{o['id']}/cancel")['status']=='cancelled'
    d=post(client,'orders',{**body,'mode':'delivery','confirmed':True})
    result=post(client,'simulation/tick',{'seconds':120})
    assert next(o for o in result['orders'] if o['id']==d['id'])['status']=='delivered'
    assert client.post('/api/orders',json={**body,'facility':'food-south','mode':'delivery','confirmed':True}).status_code==400

def test_websocket_order_and_recovery(client):
    with client.websocket_connect('/ws/live') as ws:
        first=ws.receive_json()
        assert first['type']=='snapshot'
        post(client,'need',{'need':'restroom'})
        second=ws.receive_json()
        assert second['stateVersion']>first['stateVersion']
        assert {'type','timestamp','sessionId','stateVersion','payload'}<=second.keys()
    with client.websocket_connect('/ws/live') as ws:
        assert ws.receive_json()['payload']['snapshot']['fan']['need']=='restroom'

def test_reset_and_event_replay(client):
    old=client.get('/api/state').json()
    post(client,'scenario',{'scenario':'steady'});post(client,'trips/start')
    reset=post(client,'reset')
    assert reset['sessionId']!=old['sessionId']
    assert reset['stateVersion']>old['stateVersion']
    assert reset['fan']['trip'] is None
    assert reset['state']['scenario']=='critical'
    events=client.get('/api/events').json()
    assert events[-1]['payload']['snapshot']['state']==reset['state']

def test_multi_fan_and_experiments(client):
    post(client,'scenario',{'scenario':'steady'})
    for i in range(8):
        post(client,'fans',{'id':str(i),'need':'restroom'})
    assignments=client.get('/api/crowdflow').json()
    assert len(assignments)==9
    for i in range(8): post(client,f'fans/{i}/trip')
    post(client,'simulation/tick',{'seconds':30})
    assert len(client.app.state.runtime.fans)==9
    assert experiment(42)==experiment(42)
    assert experiment(42)!=experiment(43)
    result=client.get('/api/experiments?seed=42&fans=30').json()
    for run in result['runs'].values():
        assert run['metrics']['queueMinutes']==round(sum(e['queueMinutes'] for e in run['events']),3)
    assert client.get('/api/analytics').json()['eventCount']>0

@pytest.mark.parametrize('mode',['stale','unsafe','invalid','timeout','auth','fallback'])
def test_agent_guards(mode):
    rt=create_app(Settings(database_url='sqlite:///:memory:',agent_timeout_seconds=.001)).state.runtime
    async def invoke(snapshot):
        if mode=='timeout': await asyncio.sleep(1)
        if mode=='auth': raise PermissionError('secret must not be recorded')
        if mode=='invalid': return {'madeUp':'invalid'}
        return dict(sessionId='old' if mode=='stale' else rt.session,stateVersion=rt.version,action='GO',destination='imaginary',summary='unsafe')
    trace=asyncio.run(evaluate(rt,None if mode=='fallback' else invoke))
    assert not trace['success']
    assert rt.recommendation()['action']=='STAY'
    assert 'secret' not in str(trace)
    if mode=='unsafe': assert trace['safetyOverride']

def test_auth_and_origin():
    with TestClient(create_app(Settings(database_url='sqlite:///:memory:',api_token='test-token'))) as c:
        assert c.get('/api/state').status_code==401
        assert c.get('/api/state',headers={'Authorization':'Bearer test-token'}).status_code==200
        with c.websocket_connect('/ws/live') as ws:
            ws.send_json({'token':'test-token'})
            assert ws.receive_json()['type']=='snapshot'

def test_live_localhost_origin_and_snapshot_request(client):
    with client.websocket_connect('/ws/live',headers={'origin':'http://127.0.0.1:5173'}) as ws:
        initial=ws.receive_json()
        ws.send_json({'type':'snapshot_request'})
        assert ws.receive_json()['stateVersion']==initial['stateVersion']

def test_trip_analytics_are_reduced_from_events(client):
    post(client,'scenario',{'scenario':'timeout'});post(client,'need',{'need':'restroom'})
    post(client,'trips/start');post(client,'simulation/tick',{'seconds':120})
    metrics=client.get('/api/analytics').json()
    rows=[e['payload']['details'] for e in client.get('/api/events').json() if e['type']=='trip_measurement']
    assert metrics['walkingMeters']>0
    assert metrics['tripSeconds']==round(sum(r['seconds'] for r in rows),3)
    assert metrics['walkingMeters']==round(sum(r['walkingMeters'] for r in rows),3)

def test_closure_during_trip_and_automatic_progress(client):
    post(client,'scenario',{'scenario':'steady'});post(client,'trips/start')
    destination=client.app.state.runtime.fan.trip['destination']
    result=post(client,f'facilities/{destination}',{'open':False})
    assert result['fan']['trip']['status']=='returning'
    assert post(client,'simulation/auto',{'enabled':True})['automatic']
    assert not post(client,'simulation/auto',{'enabled':False})['automatic']

def test_concurrent_mutations_have_unique_event_versions(client):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses=list(pool.map(lambda need:client.post('/api/need',json={'need':need}),['food','restroom','shop','food']*3))
    assert all(r.status_code==200 for r in responses)
    events=client.get('/api/events').json()
    versions=[e['stateVersion'] for e in events]
    assert versions==sorted(set(versions))

def test_explainable_risk_and_delivery_alternative(client):
    critical=client.get('/api/state').json()['recommendation']
    assert critical['riskScore']>=75
    assert critical['riskBreakdown']
    assert sum(item['points'] for item in critical['riskBreakdown'])>=critical['riskScore']
    post(client,'preferences',{'accessible':False,'delivery':True,'speed':72})
    rec=client.get('/api/state').json()['recommendation']
    assert rec['bestAlternative']['type']=='delivery'
    assert rec['recommendedMode']=='delivery'
    assert rec['bestAlternative']['facility']=='food-north'


def test_crowdflow_experiment_has_distinct_measurable_story():
    result=experiment(42,30)
    assert result['scorecard']['unsafeDeparturesAvoided']>0
    assert result['scorecard']['highRiskMinutesAvoided']>0
    assert result['scorecard']['crowdPeakConcentrationReductionPct']>0
    before=result['scorecard']['crowdPeakConcentrationBeforePct']
    after=result['scorecard']['crowdPeakConcentrationAfterPct']
    assert after<before

def test_proof_center_exposes_live_evidence(client):
    proof=client.get('/api/proof').json()
    assert proof['label']=='LIVE DECISION EVIDENCE'
    assert proof['risk']['score']>=75
    assert proof['finalDecision']['action']=='STAY'
    assert proof['finalDecision']['assurance'] in {'HIGH','MEDIUM','CONSERVATIVE'}
    assert proof['ibmExecution']['verified'] is False
    assert proof['options']


def test_proof_center_explains_accessibility_rejection(client):
    post(client,'scenario',{'scenario':'steady'})
    post(client,'need',{'need':'shop'})
    post(client,'preferences',{'accessible':True,'delivery':False,'speed':72})
    proof=client.get('/api/proof').json()
    assert proof['finalDecision']['action']=='WAIT'
    checks=proof['accessibility']['checks']
    assert checks and checks[0]['eligible'] is False
    assert 'accessible' in checks[0]['why'].lower() or 'eligible route' in checks[0]['why'].lower()


def test_evaluation_lab_is_computed_and_100_cases(client):
    result=client.get('/api/evaluation').json()
    assert result['total']==100
    assert result['passed']+result['failed']==100
    assert sum(c['total'] for c in result['categories'])==100
    assert len(result['cases'])==100
    assert result['passRatePct']==round(result['passed'],1)


def test_evaluation_categories_have_expected_sizes(client):
    result=client.get('/api/evaluation').json()
    sizes={c['id']:c['total'] for c in result['categories']}
    assert sizes=={'highRisk':30,'safeWindow':30,'queueSpike':20,'accessibility':10,'facilityClosure':10}
