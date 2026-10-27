# SPDX-License-Identifier: AGPL-3.0-only
# Ported conversation/provider assertions from legacy 9e89fa1; no legacy engine fixture.
import asyncio,json,time
import httpx,pytest
from dataclasses import replace
from pathlib import Path
from companion_ai.conversation import ConversationService,ModelManager,OllamaAdapter
from companion_ai.models import AIConfig,MemoryConfig,SpeechPolicy
from companion_ai.context import compose_messages,ContextBudgetError
from companion_ai.director import ConversationDirector,DirectorConfig,repetition,numerical_request
from companion_ai.llm import OllamaProvider,ChatMessage,LLMRequest,ToolDefinition,ToolCall,LLMEvent,NoVisibleResponseError
from companion_ai.storage import SettingsStore
from tests.ai.support import ObservationFixture
def runtime_fixture(visible_on_retry=True):
    calls=[]
    def handler(request):
        body=json.loads(request.content) if request.content else {}
        if request.url.path=='/api/show':
            return httpx.Response(200,json={'system':'I am Evelyn.','capabilities':['completion','thinking','tools'],'model_info':{'test.context_length':8192}})
        if request.url.path=='/api/ps':
            return httpx.Response(200,json={'models':[]})
        if request.url.path=='/api/generate':
            return httpx.Response(200,json={'done':True})
        calls.append(body)
        row={'message':{'thinking':'PRIVATE REASONING'},'done':True,'done_reason':'length','eval_count':body['options']['num_predict']}
        if visible_on_retry and len(calls)>1:
            row={'message':{'content':'Good morning! Evelyn here.'},'done':True,'done_reason':'stop'}
        return httpx.Response(200,text=json.dumps(row)+'\n')
    return httpx.MockTransport(handler),calls


async def test_text_only_reasoning_exhaustion_retries_once_without_disabling_thinking():
    transport,calls=runtime_fixture()
    manager=ModelManager(transport=transport)
    await manager.start(AIConfig(model='evelyn-v11:latest'))
    chunks=[]
    result=await manager.reply({'conversation_source':'user'},'Hello Evelyn',[],on_chunk=chunks.append)
    assert result=='Good morning! Evelyn here.' and chunks==[result]
    assert [call['options']['num_predict'] for call in calls]==[2048,4096]
    assert all(call['think'] is True and not call.get('tools') for call in calls)
    assert calls[0]['messages']==calls[1]['messages']
    assert manager.config.max_tokens==2048 and manager.config.thinking
    assert manager.metrics.samples[-1]['output_budget']==4096
    assert 'PRIVATE' not in json.dumps(list(manager.metrics.samples))
    await manager.stop()


async def test_reasoning_retry_is_bounded_and_reports_actual_failed_budget():
    transport,calls=runtime_fixture(visible_on_retry=False)
    manager=ModelManager(transport=transport)
    await manager.start(AIConfig(model='evelyn-v11:latest'))
    with pytest.raises(NoVisibleResponseError,match='4096 output tokens'):
        await manager.reply({'conversation_source':'user'},'Hello',[])
    assert len(calls)==2 and all(call['think'] for call in calls)
    assert manager.load_state=='error'
    await manager.stop()


async def test_reasoning_retry_shares_one_total_deadline():
    class Slow:
        calls=0
        async def stream(self,request):
            self.calls+=1
            await asyncio.sleep(.6 if self.calls==1 else 10)
            raise NoVisibleResponseError(request.config,'length')
            yield
    manager=ModelManager();manager.mode='ollama';manager.config=AIConfig(timeout_seconds=1.0);manager.adapter=Slow()
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(manager.reply({},'Hello',[]),1.5)
    assert manager.adapter.calls==2
