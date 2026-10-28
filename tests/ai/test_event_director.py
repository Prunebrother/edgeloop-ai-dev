# SPDX-License-Identifier: AGPL-3.0-only
import asyncio,json
import pytest
from companion_ai.conversation import ConversationService,ModelManager
from companion_ai.models import AIConfig
from companion_ai.director import DirectorConfig
from companion_ai.event_intelligence import EventConfig
from ai_observer.observation import ObserverDirector
from tests.fork.event_replay import Replay
from tests.ai.test_f25 import runtime

async def service(config=None,text='[[expression:focused]]The simulator shows a measured increase. No cause is established.'):
 r=Replay(config);wire=[];m=ModelManager(transport=runtime(wire,text));await m.select(AIConfig(model='evelyn-narrative-v1:latest'));m.current_summary=r.observation.summary
 d=ObserverDirector(DirectorConfig(regenerate_once=False),clock=r.clock.mono)
 frames=[];s=ConversationService(r.observation,frames.append,m,clock=r.clock.mono,director=d);s.event_intelligence=r.detector
 for i in range(21):s.process_derived(r.step(85+i,seconds=0 if i==0 else 1))
 return r,s,wire,frames

async def test_derived_response_uses_actual_evidence_thinking_off_and_no_cause():
 r,s,wire,frames=await service(text='[[expression:focused]]The simulator endpoint medians rose from 86 BPM to 104 BPM, a change of 18 BPM. No cause is established.')
 assert s.pending and len(s.pending)==1;s.director.session_status='RUNNING';s.pump();await s.task
 assert len(wire)==1 and wire[0][1]['think'] is False
 assert 'DERIVED TELEMETRY OBSERVATION' in wire[0][1]['messages'][-1]['content']
 assert any(f['type']=='speech' and f['expression']=='focused' for f in frames)
 assert s.event_intelligence.history[-1]['decision']=='acknowledged'
 assert s.narrative.state['event_references'] and not any('bpm' in json.dumps(e).lower() for e in s.narrative.state['event_references'])
 assert 'PRIVATE REASONING' not in json.dumps(list(s.history))
 await s.close()

async def test_typing_active_user_and_epoch_prevent_unwanted_commentary():
 r,s,wire,frames=await service();s.director.typing_until=r.clock.mono()+6;s.pump()
 assert not s.task and 'user_typing' in s.event_intelligence.history[-1]['decision']
 old=list(s.history);s.reset_narrative();assert not s.pending and list(s.history)==old
 assert s.event_intelligence.history[-1]['decision']=='discarded:storyline_reset'
 s.pump();assert not wire
 await s.close()

@pytest.mark.parametrize('mode',['routine','irrelevant','disabled'])
async def test_context_only_or_disabled_never_generates(mode):
 c=EventConfig()
 if mode=='routine':c.detectors['rapid_rise'].significance='routine'
 elif mode=='irrelevant':c.preferences['evelyn']['physiology']=0
 elif mode=='disabled':c.enabled=False
 r,s,wire,frames=await service(c);s.pump();assert not s.task and not wire
 if mode!='disabled':assert 'context_only' in s.event_intelligence.history[-1]['decision']
 await s.close()

async def test_configuration_session_and_model_changes_discard_pending():
 r,s,wire,frames=await service();s.configure_events(EventConfig());assert not s.pending
 assert s.event_intelligence.history[-1]['decision']=='discarded:configuration_changed'
 await s.close()
 r,s,wire,frames=await service();r.step(120,reset=True);s.pump();assert not s.pending and not wire
 await s.close()
 r,s,wire,frames=await service();s.adapter.config=AIConfig(model='daisy-narrative-v1:latest');s.activate_model()
 assert not s.pending and 'model_switch' in s.event_intelligence.history[-1]['decision']
 await s.close()

async def test_proactive_disabled_retains_diagnostic_without_pending_replay():
 r,s,wire,frames=await service();s.pending.clear();s.director.config.spontaneous_enabled=False
 s.enqueue('rapid_rise',45,{'event_id':s.event_intelligence.history[-1]['event']['id'],'category':'derived'})
 assert not s.pending and not wire and 'proactive_disabled' in s.event_intelligence.history[-1]['decision']
 await s.close()
