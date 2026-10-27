"""AGPL-3.0-only. F2 observer service reusing existing AI classes, no engine.
Run through tools/serve-ai.sh; import has no application/controller side effects.
"""
import asyncio
from contextlib import asynccontextmanager, suppress
import json
import logging
import os
from pathlib import Path
import secrets
import time
from uuid import uuid4
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import ValidationError
from companion_ai.conversation import ModelManager, ConversationService
from companion_ai.director import ConversationDirector, DirectorConfig
from companion_ai.llm import thinking_support
from companion_ai.models import AIConfig, SpeechPolicy
from companion_ai.storage import SettingsStore
from .config import RuntimeConfig, validate_ollama_url
from .protocol import Auth, Messages, Observation, Chat, Select, Models, Cancel, safe_validation_errors
from .observation import BrowserObservation, ObserverDirector

DEFAULT_ORIGINS=frozenset({'http://127.0.0.1:8770','http://localhost:8770'})

def create_app(token, data_dir, *, origins=DEFAULT_ORIGINS, adapter=None, transport=None, clock=time.monotonic, ollama_url=None):
    if not 32<=len(token)<=128: raise ValueError('A 32–128 character pairing token is required')
    state=BrowserObservation(clock)
    store=SettingsStore(data_dir)
    endpoint=validate_ollama_url(ollama_url) if ollama_url is not None else RuntimeConfig.load().ollama_url
    manager=ModelManager(endpoint,store=store,transport=transport)
    manager.current_summary=state.summary
    director=ObserverDirector(DirectorConfig.model_validate(store.read('director.json',{})),clock=clock)
    queues=set();owner=None;expires=clock()+3600;model_lock=asyncio.Lock()
    def publish(message):
        # No callback from model output to EdgeLoop. Messages are presentation only.
        if len(json.dumps(message,allow_nan=False).encode())>65536:
            message={'type':'ai_error','detail':'AI response exceeds the presentation limit'}
        for q in tuple(queues):
            if q.full():
                while not q.empty():q.get_nowait()
                q.put_nowait({'type':'resync_required'})
            else:q.put_nowait(message)
    speech=ConversationService(state,publish,adapter or manager,clock=clock,director=director)
    speech.policy=SpeechPolicy(event_responses=False) # User chat only in F2; Director retains observations.

    async def interrupt():
        speech.interrupt()
        await asyncio.gather(*tuple(speech.tasks),return_exceptions=True)

    async def maintenance():
        while True:
            await asyncio.sleep(.25)
            if owner and clock()>expires:
                await owner['ws'].close(code=1008);continue
            if owner and state.connected and not state.fresh():
                state.connected=False;speech.pending.clear();speech.interrupt()
                publish({'type':'telemetry_status','fresh':False})

    @asynccontextmanager
    async def lifespan(app):
        task=asyncio.create_task(maintenance())
        try:yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):await task
            await speech.close()
            with suppress(ValueError,httpx.HTTPError):await manager.stop()

    app=FastAPI(title='EdgeLoop read-only AI observer',lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
    app.state.observation=state;app.state.models=manager;app.state.speech=speech;app.state.director=director
    @app.middleware('http')
    async def origin_guard(request:Request,call_next):
        if request.headers.get('origin') not in {None,*origins}:
            return JSONResponse({'detail':'Origin refused'},status_code=403)
        response=await call_next(request);response.headers['Cache-Control']='no-store';return response
    @app.get('/health')
    async def health():return {'ok':True,'read_only':True,'engine':'original_browser','observation_fresh':state.fresh(),'ollama_url':endpoint}

    @app.websocket('/observe')
    async def observe(ws:WebSocket):
        nonlocal owner
        if ws.headers.get('origin') not in origins:
            await ws.close(code=1008);return
        await ws.accept()
        q=asyncio.Queue(maxsize=32);ai_queue=asyncio.Queue(maxsize=8);identity={'ws':ws};tasks=[]
        try:
            raw=await asyncio.wait_for(ws.receive_text(),timeout=5)
            if len(raw.encode())>16384:await ws.close(code=1009);return
            auth=Auth.model_validate_json(raw)
            if clock()>expires or not secrets.compare_digest(auth.token.encode(),token.encode()):
                await ws.close(code=1008);return
            if owner:
                if owner['browser_id']!=auth.browser_id:
                    await ws.close(code=1008);return
                await owner['ws'].close(code=1000)
            identity.update(browser_id=auth.browser_id,epoch=str(uuid4()))
            speech.pending.clear();speech.interrupt()
            owner=identity;queues.add(q);state.begin_epoch()
            seen={};last_observation=float('-inf');chat_times=[]
            await ws.send_json({'type':'ready','version':1,'epoch':identity['epoch'],'read_only':True})

            async def send():
                while True:
                    m=await q.get();await asyncio.wait_for(ws.send_json(m),timeout=2)
                    if m['type']=='resync_required':await ws.close(code=1013);return
            async def receive():
                nonlocal last_observation
                while True:
                    raw=await ws.receive_text()
                    if owner is not identity or clock()>expires:await ws.close(code=1008);return
                    if len(raw.encode())>16384:await ws.close(code=1009);return
                    try:message=Messages.validate_json(raw)
                    except ValidationError as exc:
                        # Field paths/codes are diagnostic; never log raw input, chat or tokens.
                        errors=safe_validation_errors(exc)
                        logging.getLogger(__name__).warning('Rejected read-only message fields=%s',errors)
                        publish({'type':'protocol_error','detail':'Invalid read-only message','errors':errors});continue
                    if isinstance(message,Observation):
                        if message.epoch!=identity['epoch']:
                            publish({'type':'observation_ack','accepted':False,'reason':'epoch'});continue
                        # Latest-state protocol, not a telemetry backlog. Bound flood processing.
                        now=clock()
                        previous=state.report
                        urgent=previous and ((message.snapshot.status in {'PAUSED','IDLE'} and message.snapshot.status!=previous['status']) or
                            message.snapshot.safety.signal=='stale' and previous['safety']['signal']!='stale')
                        if now-last_observation<.1 and not urgent:
                            publish({'type':'observation_ack','accepted':False,'reason':'rate_limit'});continue
                        if not state.accept(message):
                            publish({'type':'observation_ack','accepted':False,'reason':'sequence'});continue
                        last_observation=now
                        director.session_status=state.status
                        director.observation('snapshot',{'status':state.status},'edgeloop_telemetry')
                        seen_keys=list(seen)
                        for key in seen_keys:
                            if now-seen[key]>300:seen.pop(key)
                        for event in message.events:
                            # Only proven source transitions can reach dialogue/event pacing.
                            if event.id not in state.accepted_event_ids:continue
                            if event.id in seen:continue
                            seen[event.id]=now
                            if len(seen)>256:seen.pop(next(iter(seen)))
                            if event.kind in {'pause','stop'} and state.status in {'PAUSED','IDLE'} and previous and state.status!=previous['status']:
                                speech.safety(event.kind)
                            elif event.kind=='signal_lost' and state.status=='PAUSED' and previous and previous['safety']['signal']!='stale':speech.safety('signal_lost')
                            else:speech.enqueue(event.kind,30 if event.kind=='edge' else 10,{'edge_count':message.snapshot.edges})
                        publish({'type':'observation_ack','accepted':True,'sequence':message.sequence,'session_id':state.session_id,
                            'events':[{'id':e.id,'kind':e.kind,'session_id':state.session_id} for e in message.events if e.id in state.accepted_event_ids]})
                    elif isinstance(message,Cancel):
                        # Interrupt output immediately, independently of telemetry/model discovery.
                        speech.pending.clear();speech.interrupt()
                        # Drop chats still waiting on discovery/selection, retaining non-chat work.
                        retained=[]
                        while not ai_queue.empty():
                            queued=ai_queue.get_nowait()
                            if not isinstance(queued,Chat):retained.append(queued)
                        for queued in retained:ai_queue.put_nowait(queued)
                    else:
                        if ai_queue.full():publish({'type':'ai_error','detail':'AI request queue is full'})
                        else:ai_queue.put_nowait(message)
            async def process_ai():
                while True:
                    message=await ai_queue.get()
                    if owner is not identity:return
                    if isinstance(message,Models):
                        try:
                            provider=manager.provider()
                            available=await asyncio.wait_for(provider.discover(),timeout=10)
                            publish({'type':'models','models':[{'name':m['name']} for m in available[:128]],'selected':manager.config.model,'ollama_url':endpoint})
                        except (ValueError,httpx.HTTPError,TimeoutError):publish({'type':'ai_error','code':'discovery_unavailable','detail':'Ollama model discovery unavailable at '+endpoint,'ollama_url':endpoint})
                    elif isinstance(message,Select):
                        try:
                            async with model_lock:
                                presets=store.read('model-presets.json',{})
                                values=manager.config.model_dump() | presets.get(manager.preset_key(message.selection.model),presets.get(manager.config.provider+':'+message.selection.model,{})) | {'model':message.selection.model}
                                if message.thinking is not None:values['thinking']=message.thinking
                                # Models without reasoning support remain usable with thinking off.
                                metadata=await manager.provider(AIConfig.model_validate(values)).capabilities(message.selection.model)
                                controls=thinking_support(metadata)
                                supports_thinking=controls['can_enable']
                                if message.thinking is None:
                                    if not controls['can_enable']:values['thinking']=False
                                    elif not controls['can_disable']:values['thinking']=True
                                if message.selection.context_length is not None:values['context_length']=message.selection.context_length
                                await manager.select(AIConfig.model_validate(values),message.selection.context_policy,interrupt)
                                speech.activate_model()
                                publish({'type':'model_selected','model':manager.config.model,'thinking':manager.config.thinking,'supports_thinking':supports_thinking,'can_disable_thinking':controls['can_disable'],'history':[{k:str(m[k])[:4000] for k in ('role','content')} for m in list(speech.history)[-8:]]})
                        except (ValueError,httpx.HTTPError,OSError):publish({'type':'ai_error','detail':'Model settings could not be applied; check model availability and thinking support.', 'selection_failed':True,'active':manager.mode not in {'mock','stopped'}})
                    elif isinstance(message,Chat):
                        chat_times[:]=[t for t in chat_times if clock()-t<60]
                        if len(chat_times)>=12:publish({'type':'ai_error','detail':'Chat rate limit'});continue
                        chat_times.append(clock())
                        async with model_lock:
                            if not adapter and (manager.mode in {'mock','stopped'} or message.model!=manager.config.model):
                                publish({'type':'ai_error','detail':'Select an installed model before sending; no simulator reply substituted'});continue
                            speech.request(message.text,user=True)
            tasks=[asyncio.create_task(send()),asyncio.create_task(receive()),asyncio.create_task(process_ai())]
            done,_=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for task in done:task.result()
        except (ValidationError,TimeoutError,KeyError):
            with suppress(RuntimeError):await ws.close(code=1008)
        except (WebSocketDisconnect,RuntimeError,asyncio.CancelledError):pass
        finally:
            queues.discard(q)
            for task in tasks:task.cancel()
            with suppress(asyncio.CancelledError):await asyncio.gather(*tasks,return_exceptions=True)
            if owner is identity:
                owner=None;state.connected=False;speech.pending.clear();speech.interrupt()

    return app


def main():
    import argparse
    import socket
    import errno
    import uvicorn
    parser=argparse.ArgumentParser(description='Read-only EdgeLoop observer; uses an existing local Ollama server.')
    parser.add_argument('--check',action='store_true',help='Print configuration and verify Ollama discovery; do not start any server')
    args=parser.parse_args()
    try:config=RuntimeConfig.load()
    except (ValueError,OSError) as exc:parser.error(str(exc))
    print('Ollama endpoint: '+config.ollama_url,flush=True)
    if args.check:
        try:
            with httpx.Client(base_url=config.ollama_url,timeout=5,trust_env=False) as client:
                response=client.get('/api/tags');response.raise_for_status()
                names=[m['name'] for m in response.json().get('models',[])]
            print('Installed models ('+str(len(names))+'): '+', '.join(names))
        except (httpx.HTTPError,ValueError,KeyError) as exc:
            parser.exit(1,'Ollama is unavailable at '+config.ollama_url+'. Start that existing server manually or set EDGELOOP_OLLAMA_URL. No process was started.\n')
        return
    try:
        with socket.socket() as probe:probe.bind(('127.0.0.1',config.port))
    except OSError as exc:
        detail=f'Observer port {config.port} is occupied.' if exc.errno==errno.EADDRINUSE else f'Cannot bind observer port {config.port}: {exc.strerror}.'
        parser.exit(1,detail+' Inspect ss -ltnp or choose EDGELOOP_OBSERVER_PORT. No process was stopped.\n')
    token=secrets.token_urlsafe(32)
    print('Read-only observer. Pairing token (valid for this process, 1 hour): '+token,flush=True)
    app=create_app(token,config.data_dir,ollama_url=config.ollama_url)
    uvicorn.run(app,host='127.0.0.1',port=config.port,workers=1,ws_max_size=16384,access_log=False)

if __name__=='__main__':main()
