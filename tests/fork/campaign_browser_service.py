# SPDX-License-Identifier: AGPL-3.0-only
"""Campaign browser fixture: the real observer with mocked Ollama (tests/fork/browser_service.py).

/fixture/campaign/evidence hands the campaign one synthetic observer report. It stands in for a
real heart-rate strap and toy, which a browser test cannot connect; the shipping app has no such path."""
import os
import httpx
import uvicorn
from fastapi import Request
from ai_observer.server import create_app
from tests.fork.browser_service import runtime, TOKEN, UI_PORT, OBSERVER_PORT
from companion_ai.campaign import PROGRESS_FILE

DATA = os.environ['EDGELOOP_CAMPAIGN_FIXTURE_DATA']
app = create_app(TOKEN, DATA, transport=httpx.MockTransport(runtime), origins={f'http://127.0.0.1:{UI_PORT}'})


@app.post('/fixture/campaign/evidence')
async def evidence(request: Request):
    body = await request.json()
    sent = app.state.campaign.observe(body['report'], body.get('events', []), app.state.models.config.model)
    for message in sent: app.state.speech.publish(message)
    return {'sent': [m['type'] for m in sent], 'model': app.state.models.config.model}


@app.get('/fixture/campaign')
async def progress():
    path = os.path.join(DATA, PROGRESS_FILE)
    return {'saved': open(path).read() if os.path.exists(path) else None, 'model': app.state.models.config.model}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=OBSERVER_PORT, access_log=False, ws_max_size=16384)
