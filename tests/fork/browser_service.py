"""Isolated browser fixture: real observer classes, mocked local model transport."""
from pathlib import Path
import os
import asyncio
import json
import re
import tempfile
import httpx
import uvicorn
from ai_observer.server import create_app

UI_PORT=int(os.getenv('EDGELOOP_FIXTURE_UI_PORT','8770'))
OBSERVER_PORT=int(os.getenv('EDGELOOP_FIXTURE_OBSERVER_PORT','8768'))
last_thinking=None
ollama_down=False
TOKEN='browser-fixture-token-'+('x'*32)
class Stream(httpx.AsyncByteStream):
    async def __aiter__(self):
        await asyncio.sleep(.3)
        for i in range(120):
            yield (json.dumps({'message':{'content':'A streamed companion message, with room to read and reflect. '*3},'done':False})+'\n').encode()
            await asyncio.sleep(.04)
        yield b'{"message":{"content":""},"done":true}\n'

async def runtime(request):
    global last_thinking
    if request.url.path=='/api/tags' and ollama_down:raise httpx.ConnectError('fixture unavailable')
    if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':name} for name in json.loads((Path(__file__).resolve().parents[1]/'fixtures/character-models.json').read_text())]})
    if request.url.path=='/api/show':return httpx.Response(200,json={'system':'Exact fixture Modelfile identity','capabilities':['completion','thinking'],'thinking':{'values':[True,False]},'model_info':{'qwen35.context_length':8192}})
    if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[]})
    body=json.loads(request.content)
    last_thinking=body.get('think')
    if 'messages' not in body:return httpx.Response(200,json={'done':True})
    if any(m.get('content')=='long streaming response' for m in body['messages']):return httpx.Response(200,stream=Stream())
    if body['messages'][-1].get('content')=='thinking cutoff test':
        retry=body['options']['num_predict']>2048
        return httpx.Response(200,text=json.dumps({'message':{'content':'Finished after reasoning.' if retry else 'UNFINISHED_DRAFT'},'done':True,'done_reason':'stop' if retry else 'length'})+'\n')
    context=body['messages'][0]['content'];match=re.search(r'"hr":(\d+)',context)
    hr=match[1] if match else 'unknown'
    return httpx.Response(200,text=json.dumps({'message':{'content':body['model']+' reports '+hr+' BPM.'},'done':True})+'\n')
app=create_app(TOKEN,tempfile.mkdtemp(prefix='fork-browser-fixture-'),transport=httpx.MockTransport(runtime),origins={f'http://127.0.0.1:{UI_PORT}'})
@app.post('/fixture/ollama-down')
async def disconnect_ollama():
    global ollama_down
    ollama_down=True
    return {'ok':True}

@app.get('/fixture/state')
async def observed():
    return {'state':app.state.observation.report,'director':dict(app.state.director.counts),'read_only':app.state.models.tool_executor is None,'thinking':app.state.models.config.thinking,'last_thinking':last_thinking}
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=OBSERVER_PORT,access_log=False,ws_max_size=16384)
