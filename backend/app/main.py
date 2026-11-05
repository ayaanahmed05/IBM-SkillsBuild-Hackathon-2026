import asyncio
import contextlib
import hmac
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings
from .store import Store
from .runtime import Runtime, now
from .models import ScenarioInput, NeedInput, Preferences, FacilityChange, Tick, Auto, OrderInput, Fan, Snapshot
from .engine import CATALOG
from .analytics import summarize, experiment, assignments
from .agents import evaluate


def create_app(settings=None):
    settings=settings or Settings()
    rt=Runtime(Store(settings.database_url),settings)
    tasks=set()
    def trigger():
        task=asyncio.create_task(evaluate(rt));tasks.add(task);task.add_done_callback(tasks.discard)

    async def ticker():
        while True:
            await asyncio.sleep(1)
            if rt.auto:
                async with rt.lock:
                    was_paused=rt.game['paused']
                    rt.tick(1)
                    if was_paused!=rt.game['paused']:
                        trigger()

    @asynccontextmanager
    async def lifespan(app):
        task=asyncio.create_task(ticker())
        yield
        task.cancel()
        for pending in tasks:
            pending.cancel()
        await asyncio.gather(task,*tasks,return_exceptions=True)
        rt.store.engine.dispose()

    app=FastAPI(title='FanFlow MomentGuard',lifespan=lifespan)
    app.state.runtime=rt
    app.add_middleware(CORSMiddleware,allow_origins=list({settings.frontend_origin, 'http://127.0.0.1:5173'} if settings.frontend_origin=='http://localhost:5173' else {settings.frontend_origin}),allow_methods=['GET','POST'],allow_headers=['Content-Type','Authorization'])

    @app.middleware('http')
    async def auth(request:Request,call_next):
        if settings.api_token and request.url.path!='/api/health' and request.method!='OPTIONS':
            if not hmac.compare_digest(request.headers.get('authorization',''),f'Bearer {settings.api_token}'):
                return JSONResponse({'error':'Unauthorized'},status_code=401)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid(request,exc):
        return JSONResponse({'error':'Invalid request','details':[{'field':list(e['loc']),'message':e['msg']} for e in exc.errors()]},status_code=400)

    @app.exception_handler(ValueError)
    async def bad_value(request,exc):
        return JSONResponse({'error':str(exc)},status_code=400)

    @app.get('/api/health')
    async def health():
        return dict(ok=True,service='FanFlow MomentGuard API',mode='simulated-data')

    @app.get('/api/state',response_model=Snapshot)
    async def state():
        return rt.snapshot()

    @app.post('/api/scenario',response_model=Snapshot)
    async def scenario(body:ScenarioInput):
        async with rt.lock:
            rt.set_scenario(body.scenario);rt.replan();rt.emit('game_update');trigger()
            return rt.snapshot()

    @app.post('/api/need',response_model=Snapshot)
    async def need(body:NeedInput):
        async with rt.lock:
            rt.fan.need=body.need;rt.emit('recommendation_change');trigger()
            return rt.snapshot()

    @app.post('/api/reset',response_model=Snapshot)
    async def reset():
        async with rt.lock:
            rt.reset()
            return rt.snapshot()

    @app.post('/api/preferences',response_model=Snapshot)
    async def preferences(body:Preferences):
        async with rt.lock:
            for key,value in body.model_dump().items():
                setattr(rt.fan,key,value)
            rt.replan();trigger()
            return rt.snapshot()

    @app.post('/api/simulation/tick',response_model=Snapshot)
    async def tick(body:Tick):
        async with rt.lock:
            rt.tick(body.seconds)
            return rt.snapshot()

    @app.post('/api/simulation/auto',response_model=Snapshot)
    async def auto(body:Auto):
        async with rt.lock:
            rt.auto=body.enabled;rt.emit('snapshot')
            return rt.snapshot()

    @app.post('/api/facilities/{facility_id}',response_model=Snapshot)
    async def facility(facility_id:str,body:FacilityChange):
        async with rt.lock:
            f=next((f for f in rt.facilities if f['id']==facility_id),None)
            if not f:
                raise HTTPException(404,'Unknown facility')
            f.update(body.model_dump(exclude_none=True));rt.emit('queue_update',{'facility':facility_id});rt.replan();trigger()
            return rt.snapshot()

    @app.post('/api/routes/{a}/{b}',response_model=Snapshot)
    async def route_change(a:str,b:str,body:FacilityChange):
        async with rt.lock:
            if not rt.graph.has_edge(a,b):
                raise HTTPException(404,'Unknown route connection')
            rt.graph[a][b].update(body.model_dump(exclude_none=True,exclude={'queue'}));rt.replan();trigger()
            return rt.snapshot()

    @app.post('/api/trips/start',response_model=Snapshot)
    async def start():
        async with rt.lock:
            rt.start_trip()
            return rt.snapshot()

    @app.get('/api/catalog')
    async def catalog():
        return {'simulated':True,'currency':'CAD','items':CATALOG}

    @app.post('/api/orders')
    async def order(body:OrderInput):
        async with rt.lock:
            return rt.order(body)

    @app.post('/api/orders/{order_id}/cancel')
    async def cancel(order_id:str):
        async with rt.lock:
            order=next((o for o in rt.orders if o['id']==order_id),None)
            if not order:
                raise HTTPException(404,'Unknown order')
            if order['status']!='preparing':
                raise ValueError('Only preparing orders may be cancelled')
            order['status']='cancelled';rt.emit('order_status',{'order':order_id})
            return order

    @app.post('/api/fans')
    async def fan(body:Fan):
        async with rt.lock:
            if body.id in rt.fans or body.seat not in ['seat-101','seat-102'] or body.position!=body.seat or body.trip is not None:
                raise ValueError('Fan must have a unique ID, a known seat and start seated without a trip')
            rt.fans[body.id]=body;rt.emit('snapshot')
            return body

    @app.post('/api/fans/{fan_id}/trip')
    async def fan_trip(fan_id:str):
        async with rt.lock:
            if fan_id not in rt.fans:
                raise HTTPException(404,'Unknown fan')
            rt.start_trip(rt.fans[fan_id]);return rt.snapshot()

    @app.get('/api/crowdflow')
    async def crowdflow():
        return assignments(list(rt.fans.values()),rt.game,rt.facilities,rt.graph)

    @app.get('/api/events')
    async def events(session_id:str|None=None):
        return rt.store.events(session_id or rt.session)

    @app.get('/api/analytics')
    async def analytics():
        return summarize(rt.store.events(rt.session))

    @app.get('/api/experiments')
    async def experiments(seed:int=42,fans:int=30):
        if not 1<=fans<=500:
            raise ValueError('fans must be between 1 and 500')
        result=experiment(seed,fans)
        rt.store.append(dict(type='experiment',timestamp=now(),sessionId=rt.session,stateVersion=rt.version,payload=result))
        return result

    @app.get('/api/agents')
    async def agents():
        return {'status':'unverified','ibmConfigured':False,'traces':rt.traces}

    @app.websocket('/ws/live')
    async def live(ws:WebSocket):
        origin=ws.headers.get('origin')
        allowed_origins={settings.frontend_origin}
        if settings.frontend_origin=='http://localhost:5173':
            allowed_origins.add('http://127.0.0.1:5173')
        if origin and origin not in allowed_origins:
            await ws.close(code=1008);return
        await ws.accept()
        if settings.api_token:
            try:
                auth_message=await asyncio.wait_for(ws.receive_json(),timeout=5)
                if not hmac.compare_digest(str(auth_message.get('token','')),settings.api_token):
                    await ws.close(code=1008);return
            except (TimeoutError,WebSocketDisconnect,ValueError):
                await ws.close(code=1008);return
        queue=asyncio.Queue(maxsize=32)
        rt.subscribers.add(queue)
        async def sender():
            while True:
                try:
                    event=await asyncio.wait_for(queue.get(),timeout=15)
                except TimeoutError:
                    event=dict(type='heartbeat',timestamp=now(),sessionId=rt.session,stateVersion=rt.version,payload={})
                await ws.send_json(event)
        try:
            await ws.send_json(dict(type='snapshot',timestamp=now(),sessionId=rt.session,stateVersion=rt.version,payload={'snapshot':rt.snapshot()}))
            worker=asyncio.create_task(sender())
            try:
                while True:
                    message=await ws.receive_json()
                    if message.get('type')=='snapshot_request':
                        queue.put_nowait(dict(type='snapshot',timestamp=now(),sessionId=rt.session,stateVersion=rt.version,payload={'snapshot':rt.snapshot()}))
            finally:
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError,WebSocketDisconnect,RuntimeError):
                    await worker
        except (WebSocketDisconnect,ValueError):
            pass
        finally:
            rt.subscribers.discard(queue)
    return app

app=create_app()
