import asyncio
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
from .models import Fan, Event
from .engine import seed_venue, recommend, route, CATALOG

def now():
    return datetime.now(timezone.utc).isoformat()

class Runtime:
    def __init__(self, store, settings):
        self.store, self.settings = store, settings
        self.lock = asyncio.Lock()
        self.subscribers = set()
        self.version = 0
        self.auto = settings.automatic
        self.reset()

    def reset(self):
        self.session = str(uuid4())
        self.version += 1
        self.facilities, self.graph = seed_venue()
        self.fans = {'primary': Fan()}
        self.orders, self.traces = [], []
        self.elapsed = 0
        self.set_scenario('critical')
        self.emit('snapshot', {'reset': True})

    @property
    def fan(self):
        return self.fans['primary']

    def set_scenario(self, scenario):
        data = {'critical': (106,105,102,96,0,False), 'timeout': (106,105,48,28,5,True), 'resumed':(108,107,41,91,0,False), 'steady':(82,74,378,35,10,True)}[scenario]
        a,b,clock,intensity,window,paused=data
        self.game=dict(scenario=scenario,scoreA=a,scoreB=b,clockSeconds=clock,quarter=3 if scenario=='steady' else 4,momentIntensity=intensity,availableWindowMinutes=window,paused=paused,possession='HOME',significantEvent='Decisive possession' if intensity>=75 else None,gameState={'critical':'CLOSE GAME','timeout':'PLAY PAUSED','resumed':'PLAY RESUMED','steady':'INTERMISSION'}[scenario])

    def recommendation(self, fan=None):
        return recommend(self.game,self.facilities,self.graph,fan or self.fan,self.settings.risk_threshold,self.settings.safety_buffer_minutes)

    def snapshot(self):
        rec=self.recommendation()
        state={**self.game,'clock':f"Q{self.game['quarter']} · {int(self.game['clockSeconds'])//60}:{int(self.game['clockSeconds'])%60:02d}",'need':self.fan.need,'venue':'Northstar Arena','dataMode':'SIMULATED','trip':rec['tripEstimate'],'fanAwayFromSeat': self.fan.position!=self.fan.seat}
        return deepcopy(dict(state=state,recommendation=rec,updatedAt=now(),sessionId=self.session,stateVersion=self.version,facilities=self.facilities,routeConnections=[{'from':a,'to':b,**d} for a,b,d in self.graph.edges(data=True)],fan=self.fan.model_dump(),fans=[f.model_dump() for f in self.fans.values()],orders=self.orders,agents=self.traces[-30:],automatic=self.auto,provenance={'game':{'kind':'Simulated','source':'Seeded MomentGuard provider'},'venue':{'kind':'Simulated','source':'Fictional Northstar Arena'},'ibm':{'status':'integration-ready-unverified','executionClaimed':False,'source':'Candidate watsonx Orchestrate artifacts; deterministic safety fallback remains authoritative'}}))

    def emit(self, event_type, details=None):
        self.version+=1
        event=Event(type=event_type,timestamp=now(),sessionId=self.session,stateVersion=self.version,payload={'details':details or {},'snapshot':self.snapshot()}).model_dump()
        self.store.append(event)
        for queue in tuple(self.subscribers):
            if queue.full():
                queue.get_nowait() # Every event carries a recovery snapshot.
            queue.put_nowait(event)
        return event

    def start_trip(self, fan=None):
        fan=fan or self.fan
        rec=self.recommendation(fan)
        if rec['action']!='GO':
            raise ValueError('A trip may start only with a current GO recommendation')
        plan=rec['calculation']
        fan.trip=dict(status='walking',destination=plan['destination'],plan=plan,remaining=plan['route']['minutes']*60,totalSeconds=0,walkingMeters=0)
        fan.position='junction'
        self.emit('trip_progress',{'fan':fan.id,'status':'walking'})

    def force_return(self, fan):
        home=route(self.graph,fan.position,fan.seat,fan)
        if home is None:
            fan.trip['status']='blocked'
            return
        fan.trip.update(status='returning',remaining=home['minutes']*60,returnRoute=home)

    def replan(self):
        for fan in self.fans.values():
            if not fan.trip or fan.trip['status']=='completed':
                continue
            if fan.trip['status'] in ['returning','blocked']:
                home=route(self.graph,fan.position,fan.seat,fan)
                previous=fan.trip.get('returnRoute')
                if home is None or home!=previous:
                    self.force_return(fan)
                continue
            facility=next(f for f in self.facilities if f['id']==fan.trip['destination'])
            path=route(self.graph,fan.position,facility['node'],fan)
            if not facility['open'] or path is None or self.recommendation(fan)['action']=='RETURN':
                self.force_return(fan)
            elif fan.trip['status']=='queuing':
                fan.trip['remaining']=facility['queue']/facility['capacity']*facility['service']*facility['congestion']*60
        self.emit('route_update')

    def tick(self, seconds):
        self.elapsed+=seconds
        self.game['availableWindowMinutes']=max(0,self.game['availableWindowMinutes']-seconds/60)
        if self.game['paused'] and self.game['availableWindowMinutes']==0:
            self.set_scenario('resumed')
        elif not self.game['paused']:
            self.game['clockSeconds']=max(0,self.game['clockSeconds']-seconds)
        for fan in self.fans.values():
            trip=fan.trip
            if not trip or trip['status'] in ['completed','blocked']:
                continue
            if self.recommendation(fan)['action']=='RETURN' and trip['status']!='returning':
                self.force_return(fan)
                self.emit('route_update',{'fan':fan.id,'reason':'game resumed'})
            budget=seconds
            while budget>0 and trip['status'] not in ['completed','blocked']:
                used=min(budget,trip['remaining'])
                trip['remaining']-=used
                trip['totalSeconds']+=used
                budget-=used
                distance=0
                if trip['status'] in ['walking','returning']:
                    segment=trip['plan']['route'] if trip['status']=='walking' else trip.get('returnRoute',trip['plan']['returnRoute'])
                    distance=segment['distanceMeters']*used/max(segment['minutes']*60,0.001)
                    trip['walkingMeters']+=distance
                self.emit('trip_measurement',{'fan':fan.id,'phase':trip['status'],'seconds':used,'walkingMeters':distance,'importantMomentMissed':not self.game['paused'] and self.game['momentIntensity']>=self.settings.risk_threshold})
                if trip['remaining']>0:
                    break
                f=next(f for f in self.facilities if f['id']==trip['destination'])
                if trip['status']=='walking':
                    fan.position=f['node']
                    trip.update(status='queuing',remaining=f['queue']/f['capacity']*f['service']*f['congestion']*60)
                elif trip['status']=='queuing':
                    trip.update(status='service',remaining=f['service']*60)
                elif trip['status']=='service':
                    self.force_return(fan)
                    for order in self.orders:
                        if order['facility']==f['id'] and order['status']=='ready' and order['mode']=='pickup':
                            order['status']='picked_up'
                            self.emit('order_status',{'order':order['id'],'status':'picked_up'})
                elif trip['status']=='returning':
                    fan.position=fan.seat
                    trip['status']='completed'
                self.emit('trip_progress',{'fan':fan.id,'status':trip['status']})
        for order in self.orders:
            if order['status']=='preparing' and self.elapsed>=order['readyAt']:
                order['status']='delivered' if order['mode']=='delivery' else 'ready'
                self.emit('order_status',{'order':order['id'],'status':order['status']})
        self.emit('game_update',{'elapsedSeconds':self.elapsed})

    def order(self, body):
        if not body.confirmed:
            raise ValueError('Explicit fan confirmation is required for every simulated order')
        f=next((f for f in self.facilities if f['id']==body.facility and f['need']=='food' and f['open']),None)
        item=next((i for i in CATALOG if i['id']==body.item),None)
        if not f or not item or (body.mode=='delivery' and not f['delivery']):
            raise ValueError('Item or fulfillment option is unavailable')
        order=dict(id=str(uuid4()),facility=f['id'],item=item['id'],quantity=body.quantity,priceCents=item['priceCents']*body.quantity,mode=body.mode,simulated=True,status='preparing',readyAt=self.elapsed+120,estimatedFulfillmentSeconds=120)
        self.orders.append(order)
        self.emit('order_status',{'order':order['id'],'status':'preparing'})
        return order
