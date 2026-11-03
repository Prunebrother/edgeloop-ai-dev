"""Real-model smoke test: production service, compiler and checks; synthetic Journal; no hardware."""
import argparse,asyncio,json,sys,time,traceback
import httpx
from ai_observer.observation import ObserverDirector
from companion_ai.conversation import ConversationService,ModelManager,character_identity
from companion_ai.director import DirectorConfig
from companion_ai.event_deck import Arrival,DeckSettings
from companion_ai.models import AIConfig
from companion_ai.session_journal import SessionJournal
from tests.ai.test_arrival_comparison import RESULT,Store,journal,now_ms,record
from tests.ai.test_event_deck_content import ALL,DEFINITION,play_only
from tests.fork.event_replay import Replay
from tests.ai.test_mission_completion import MISSIONS,only_mission

BASE='http://127.0.0.1:11435'
MODELS={'daisy':'daisy-narrative-f29-v014:latest','nova':'nova-narrative-f29-v011:latest','evelyn':'evelyn-narrative-f29-v013:latest','celeste':'celeste-narrative-f29-v012:latest'}
OWN={'daisy':['daisy-production','daisy-encouragement'],'nova':['nova-curiosity','nova-challenge'],'evelyn':['evelyn-observation-edges'],'celeste':['celeste-evaluation','celeste-personal']}
DEMANDING='You are strict, commanding and provocative with the participant. You expect obedience, you say so outright, and you do not soften anything.'

class Log(httpx.AsyncBaseTransport):
    def __init__(self):self.inner=httpx.AsyncHTTPTransport();self.chat=[]
    async def handle_async_request(self,request):
        started=time.monotonic()
        response=await self.inner.handle_async_request(request)
        body=b''.join([c async for c in response.aiter_raw()])
        await response.aclose()
        if request.url.path=='/api/chat':
            sent=json.loads(request.content);text='';think='';last={}
            for line in body.splitlines():
                try:row=json.loads(line)
                except ValueError:continue
                text+=row.get('message',{}).get('content','');think+=row.get('message',{}).get('thinking','') or '';last=row
            self.chat.append({'think':sent.get('think'),'tools':bool(sent.get('tools')),'prompt':sent['messages'][-1]['content'],'roles':[m['role'] for m in sent['messages']],'all':json.dumps(sent['messages']),'raw':text,'thinking_chars':len(think),'done_reason':last.get('done_reason'),'seconds':round(time.monotonic()-started,2)})
        return httpx.Response(response.status_code,headers=[(k,v) for k,v in response.headers.items() if k.lower() not in {'content-encoding','transfer-encoding','content-length'}],content=body,request=request)

class Manager(ModelManager):
    checks=None
    async def reply(self,*args,**kwargs):
        self.grounding_corrections=[]
        try:return await super().reply(*args,**kwargs)
        except Exception as exc:
            self.checks.append({'raised':type(exc).__name__,'codes':list(getattr(exc,'codes',()))});raise
        finally:self.checks.append({'corrections':list(self.grounding_corrections or [])})

class Run:
    async def build(self,identity,status='IDLE',edges=0,seconds=0):
        self.identity=identity;self.log=Log();self.frames=[];self.checks=[]
        r=self.r=Replay();r.state['devices'].update(toy_ready=True,handy=True,hr_ready=False,simulated_hr=False);r.state['safety'].update(fault='none',signal='missing')
        r.state.update(edges=edges,seconds=seconds,status=status);r.step(None,seconds=0)
        m=self.m=Manager(BASE,transport=self.log);m.checks=self.checks
        await m.select(AIConfig(model=MODELS[identity],thinking=False,timeout_seconds=180))
        m.current_summary=r.observation.summary
        self.d=ObserverDirector(DirectorConfig(),clock=r.clock.mono)
        s=self.s=ConversationService(r.observation,self.frames.append,m,clock=r.clock.mono,director=self.d)
        s.deck_settings=DeckSettings(enabled=True,countdown_seconds=0,arrival_settle_seconds=0,mission_spacing_seconds=0);s.deck_definition=DEFINITION
        s.deck_identity=character_identity(MODELS[identity])
        r.observation.model_scope=s.active_model_id
        return self
    async def go(self):
        self.s.pump()
        if self.s.task and not self.s.task.done():await self.s.task
        await asyncio.sleep(0)
    def snapshot(self,start=0,chats=0,checks=0,decisions=0):
        frames=self.frames[start:]
        return {'speech':[f['text'] for f in frames if f['type']=='speech' and f.get('source')!='safety'],'expressions':[f.get('expression') for f in frames if f['type']=='speech'],'suppressed':[f.get('reason') for f in frames if f['type']=='response_suppressed'],'errors':[f for f in frames if f['type']=='conversation_error'],
                'attempts':[{k:a[k] for k in ('raw','done_reason','seconds','think','tools','thinking_chars','roles')} for a in self.log.chat[chats:]],'prompt':self.log.chat[-1]['prompt'] if len(self.log.chat)>chats else None,'all':'\n'.join(a['all'] for a in self.log.chat[chats:]),
                'checks':self.checks[checks:],'decisions':[{k:v for k,v in d.items() if k not in {'at','scope'}} for d in list(self.d.decisions)[decisions:]]}
    def marks(self):return len(self.frames),len(self.log.chat),len(self.checks),len(self.d.decisions)

def seed_unauthorized(run,figures='I reached 77 edges after 72 minutes.'):
    """What an unauthorized Arrival must not repeat: a transcript and a story item carrying session figures."""
    s=run.s;sid=getattr(s.state,'session_id',None)
    for role,text in (('user',figures),('assistant','You logged those 77 edges in 72 minutes, and I was impressed.')):
        s.history.append({'role':role,'content':text,'origin':'real_user','trigger_origin':'real_user','session_id':sid,'narrative_epoch':s.narrative.state['epoch'],'at':0})
    s.narrative.state['developments'].append('The participant logged 77 edges in 72 minutes.')

async def arrival(identity,case,**o):
    case,_,tone=case.partition('|')
    run=await Run().build(identity);r,s=run.r,run.s;scope=s.active_model_id;now=now_ms(r)
    if tone:s.narrative.update_objective('create',{'premise':DEMANDING})
    rows=[];access=True;expect={}
    if case=='unknown-2h':
        rows=[record(scope,now_ms=now,edges=4,seconds=None,ago_days=2/24,completeness='final_duration_unavailable')]
        expect={'status':'found','edges':[4],'duration_unknown':True,'ago_days':2/24,'forbidden':['77','72','55']}
    elif case.startswith('returning'):
        ago={'returning-2h':2/24,'returning-3d':3,'returning-3w':21}[case]
        rows=[record(scope,now_ms=now,edges=7,seconds=720,ago_days=ago),record(MODELS and scope.replace(MODELS[identity],MODELS['nova' if identity!='nova' else 'daisy']),sid='other-model',now_ms=now,edges=55,seconds=5400,ago_days=.5)]
        expect={'status':'found','edges':[7],'seconds':[720],'ago_days':ago,'forbidden':['77','72','55','90 minutes','ninety']}
    elif case=='first':expect={'status':'none','forbidden':['77','72']}
    elif case=='denied':
        rows=[record(scope,now_ms=now,edges=77,seconds=4320,ago_days=3)];access=False
        expect={'status':'denied','forbidden':['77','72','seventy']}
    r.observation.journal=journal(rows,ai_access=access)
    if case!='first':seed_unauthorized(run)
    s.arrival=Arrival(scope,r.clock.mono(),s.deck_settings)
    history=s.session_history();await run.go()
    out=run.snapshot();out.update(arrival_state=s.arrival.state,arrival_reason=s.arrival.reason,lookup=history.get('status'),expect=expect)
    return [out]

CLOSINGS={'longer-more':(10,900),'shorter-fewer':(4,300),'same-longer':(7,900),'longer-fewer':(4,900),'one-more':(8,780),'five-more':(12,900),'prior-unknown':(9,530)}
async def closing(identity,case,**o):
    case,_,tone=case.partition('|')
    if case in CLOSINGS:edges,seconds=CLOSINGS[case]
    else:edges,seconds=5,600
    run=await Run().build(identity,'RUNNING',edges,seconds);r,s=run.r,run.s;now=now_ms(r)
    if tone:s.narrative.update_objective('create',{'premise':DEMANDING})
    result=dict(RESULT)|{'edges':edges,'active_running_seconds':seconds,'last_verified_running_ticks':seconds}
    d=s.deck();d._start_done=True;d._counter_baseline={'edges':edges,'seconds':seconds}
    rows=[];access=True
    expect={'status':'none','edges':[edges],'seconds':[seconds]}
    if case in CLOSINGS:
        rows=[record(s.active_model_id,now_ms=now,edges=7,seconds=720,ago_days=3)] if case!='prior-unknown' else [record(s.active_model_id,now_ms=now,edges=4,seconds=None,ago_days=3,completeness='final_duration_unavailable')]
        expect={'status':'found','edges':[edges,7,abs(edges-7)],'seconds':[seconds,720,abs(seconds-720)],'dir_edges':(edges>7)-(edges<7),'dir_seconds':(seconds>720)-(seconds<720)}
    if case=='denied':
        rows=[record(s.active_model_id,now_ms=now,edges=77,seconds=4320,ago_days=3)];access=False;expect|={'status':'denied','forbidden':['77','72','seventy']}
    r.observation.journal=journal(rows,ai_access=access)
    r.step(None,status='IDLE')
    s.enqueue('session_ended',70,{'event_id':'end:'+r.observation.session_id,'session_id':r.observation.session_id,'category':'authoritative','at_ms':now_ms(r),'session_result':result,'evidence':'Session ended.'})
    await run.go()
    out=run.snapshot();out.update(expect=expect);return [out]

async def card(identity,case,**o):
    cid,demanding=case.split('|');demanding=demanding=='demanding'
    count=3 if cid=='edge-count-first' else 5
    run=await Run().build(identity,'RUNNING',count,700);r,s=run.r,run.s
    r.observation.journal=journal([])
    if demanding:s.narrative.update_objective('create',{'premise':DEMANDING})
    s.deck();play_only(s,cid)
    await run.go()
    out=run.snapshot();out.update(expect={'edges':[count],'seconds':[700],'demanding':demanding},card=cid);return [out]

async def milestone(identity,case,**o):
    cid,edges=case.split('|')[0],int(case.split('|')[1])
    done=next(d for c,e,d in MISSIONS if c==cid)
    run=await Run().build(identity,'RUNNING',edges,300+edges*30);r,s=run.r,run.s
    r.observation.journal=journal([])
    if case.endswith('demanding'):s.narrative.update_objective('create',{'premise':DEMANDING})
    only_mission(s,done)
    await run.go()
    out=run.snapshot();out.update(expect={'edges':[edges],'milestone':edges},card=cid);return [out]

async def opening(identity,case,**o):
    run=await Run().build(identity,'RUNNING',0,0);r,s=run.r,run.s;scope=s.active_model_id;now=now_ms(r)
    d=s.deck();d._counter_baseline={'edges':0,'seconds':0}
    if case=='returning':rows,access,status=[record(scope,now_ms=now,edges=7,seconds=720,ago_days=3)],True,'found'
    elif case=='first':rows,access,status=[],True,'none'
    elif case=='denied':rows,access,status=[record(scope,now_ms=now,edges=77,seconds=4320,ago_days=3)],False,'denied'
    r.observation.journal=journal(rows,ai_access=access)
    await run.go()
    out=run.snapshot();out.update(expect={'edges':[0],'relationship':case,'forbidden':['77','72']});return [out]

async def journey(identity,case,**o):
    """Arrival, session, milestone, normal card, Closing, Arrival, session, comparative Closing, on one service and real Journal."""
    run=await Run().build(identity);r,s=run.r,run.s;scope=s.active_model_id
    r.observation.journal=SessionJournal(Store({'schema_version':1,'recording':True,'ai_access':True,'nova_cross_companion':False,'records':[]}))
    steps=[]
    async def stage(name,expect,act):
        before=run.marks();await act()
        out=run.snapshot(*before);out.update(stage=name,expect=expect,lookup=s.session_history().get('status') if name.startswith('arrival') else None);steps.append(out)
        r.clock.tick(120);r.step(None,seconds=0)
    async def session(edges,seconds,stem):
        r.state['details'].pop('terminal_outcome',None)
        r.step(None,seconds=1,status='IDLE',reset=True);r.step(None,seconds=0,status='RUNNING')
        s.director.session_status='RUNNING'
        await stage(stem+'-opening',{'edges':[0],'seconds':[0,1]},run.go)
        for mark in (3,7,10):
            if edges>=mark:
                r.state['edges']=mark;r.step(None,seconds=30)
                await stage(stem+f'-milestone-{mark}',{'edges':[mark],'milestone':mark},run.go)
        r.state['edges']=edges;r.step(None,seconds=max(1,seconds-400))
        await stage(stem+'-normal',{'edges':[edges],'seconds':[r.state['seconds']]},run.go)
        result=dict(RESULT)|{'edges':edges,'active_running_seconds':r.state['seconds'],'last_verified_running_ticks':r.state['seconds']}
        total=r.state['seconds']
        if case!='unknown':r.state['details']['terminal_outcome']='manual_stop'
        r.step(None,seconds=1,status='IDLE');s.director.session_status='IDLE'
        result|={'active_running_seconds':r.state['seconds'],'last_verified_running_ticks':r.state['seconds']}
        total=r.state['seconds']
        async def end():
            s.enqueue('session_ended',70,{'event_id':'end:'+r.observation.session_id,'session_id':r.observation.session_id,'category':'authoritative','at_ms':now_ms(r),'session_result':result,'evidence':'Session ended.'})
            await run.go()
        return end,edges,total
    s.arrival=Arrival(scope,r.clock.mono(),s.deck_settings)
    await stage('arrival-first',{'status':'none'},run.go)
    end,e1,t1=await session(4,600,'s1')
    await stage('s1-closing',{'status':'none','edges':[e1],'seconds':[t1]},end)
    r.clock.tick(7200);r.step(None,seconds=0)
    s.arrival=Arrival(scope,r.clock.mono(),s.deck_settings)
    await stage('arrival-returning',{'status':'found','edges':[e1],'ago_days':2/24}|({'duration_unknown':True} if case=='unknown' else {'seconds':[t1]}),run.go)
    end,e2,t2=await session(11,900,'s2')
    await stage('s2-closing',{'status':'found','edges':[e2,e1,abs(e2-e1)],'seconds':[t2,t1,abs(t2-t1)],'dir_edges':(e2>e1)-(e2<e1),'dir_seconds':(t2>t1)-(t2<t1)},end)
    return steps

PLAN=[('closing',c,closing,3) for c in ('shorter-fewer','longer-fewer','same-longer','one-more','five-more')]+[('closing',c+'|demanding',closing,2) for c in ('shorter-fewer','longer-fewer')]
PLAN+=[('arrival',c,arrival,3) for c in ('first','returning-2h','unknown-2h')]
PLAN+=[('milestone',f'{c}|{e}',milestone,3) for c,e,_ in MISSIONS]

async def main(a):
    who=a.who.split(',')
    out=open(a.out,'a')
    for identity in who:
        plan=list(PLAN)
        for kind,case,fn,reps in plan:
            if a.only and a.only not in f'{kind}:{case}':continue
            for rep in range(reps):
                started=time.monotonic()
                try:rows=await fn(identity,case)
                except Exception:
                    rows=[{'harness_error':traceback.format_exc()[-900:]}]
                for row in rows:
                    row.update(companion=identity,kind=kind,case=case,rep=rep,wall=round(time.monotonic()-started,1))
                    row['errors']=[str(e)[:200] for e in row.get('errors',())]
                    out.write(json.dumps(row)+'\n');out.flush()
                    print(identity,kind,case,rep,row.get('stage',''),'|',row.get('harness_error') or row.get('speech'),'| att',len(row.get('attempts',[])),'sup',row.get('suppressed'),row.get('arrival_state',''),flush=True)
ap=argparse.ArgumentParser();ap.add_argument('--who',default='daisy,nova,evelyn,celeste');ap.add_argument('--only');ap.add_argument('--second',action='store_true');ap.add_argument('--out',required=True)
asyncio.run(main(ap.parse_args()))
