"""Cloud adapter boundary. No mock is ever labelled IBM execution."""
import asyncio
from time import perf_counter
from pydantic import ValidationError
from .models import Proposal
from .runtime import now

async def evaluate(runtime, invoke=None):
    snapshot=runtime.snapshot()
    started=perf_counter()
    trace=dict(agent='MomentGuard Coordinator',provider='deterministic fallback',tool=None,timestamp=now(),input={'sessionId':snapshot['sessionId'],'stateVersion':snapshot['stateVersion']},output=None,success=False,safetyOverride=False)
    try:
        if invoke is None:
            trace['summary']='IBM account capability and execution have not been verified; deterministic engine remains authoritative.'
        else:
            raw=await asyncio.wait_for(invoke(snapshot),timeout=runtime.settings.agent_timeout_seconds)
            proposal=Proposal.model_validate(raw)
            trace['output']=proposal.model_dump()
            async with runtime.lock:
                if proposal.sessionId!=runtime.session or proposal.stateVersion!=runtime.version:
                    trace['summary']='Rejected stale proposal'
                elif proposal.action!=runtime.recommendation()['action'] or proposal.destination!=runtime.recommendation()['destination']:
                    trace['safetyOverride']=True
                    trace['summary']='Rejected unsafe or inconsistent proposal'
                else:
                    trace['summary']=proposal.summary
                    trace['success']=True
                    # Adapter must provide verified execution evidence before claiming IBM.
    except (TimeoutError,ValidationError,ValueError,PermissionError) as exc:
        trace['summary']=f'Agent evaluation failed: {type(exc).__name__}'
    except Exception:
        trace['summary']='Agent transport failed; deterministic fallback retained'
    trace['latencyMs']=round((perf_counter()-started)*1000,2)
    async with runtime.lock:
        runtime.traces.append(trace)
        runtime.emit('agent_action',{'trace':trace})
    return trace
