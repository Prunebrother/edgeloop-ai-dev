"""Isolated browser fixture: real observer classes, mocked local model transport."""
import asyncio
import json
import re
import tempfile
import httpx
import uvicorn
from ai_observer.server import create_app

TOKEN='browser-fixture-token-'+('x'*32)
class Stream(httpx.AsyncByteStream):
    async def __aiter__(self):
        for i in range(120):
            yield (json.dumps({'message':{'content':'A streamed companion message, with room to read and reflect. '*3},'done':False})+'\n').encode()
            await asyncio.sleep(.04)
        yield b'{"message":{"content":""},"done":true}\n'

async def runtime(request):
    if request.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':'mira:latest'},{'name':'evelyn:latest'}]})
    if request.url.path=='/api/show':return httpx.Response(200,json={'capabilities':['completion','thinking'],'model_info':{'qwen.context_length':8192}})
    if request.url.path=='/api/ps':return httpx.Response(200,json={'models':[]})
    body=json.loads(request.content)
    if 'messages' not in body:return httpx.Response(200,json={'done':True})
    if any(m.get('content')=='long streaming response' for m in body['messages']):return httpx.Response(200,stream=Stream())
    context=body['messages'][0]['content'];match=re.search(r'"hr":(\d+)',context)
    hr=match[1] if match else 'unknown'
    return httpx.Response(200,text=json.dumps({'message':{'content':body['model']+' reports '+hr+' BPM.'},'done':True})+'\n')
app=create_app(TOKEN,tempfile.mkdtemp(prefix='fork-browser-fixture-'),transport=httpx.MockTransport(runtime))
@app.get('/fixture/state')
async def observed():
    return {'state':app.state.observation.report,'director':dict(app.state.director.counts),'read_only':app.state.models.tool_executor is None}
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8768,access_log=False,ws_max_size=16384)
