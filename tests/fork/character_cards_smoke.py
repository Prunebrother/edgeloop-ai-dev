# SPDX-License-Identifier: AGPL-3.0-only
"""Opt-in character-card quality sample; existing local models, no device connection.

Run from the repository root:
  EDGELOOP_LIVE_ACCEPTANCE=1 python -m tests.fork.character_cards_smoke \
      --url http://127.0.0.1:11435 --output /tmp/character-cards-smoke.json
Each card is isolated to guarantee coverage with one generation per card (plus
normal bounded retries). Shuffle and duplicate delivery are tested separately.
Read the transcript: lexical repetition checks do not establish dialogue quality.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import time

import httpx

from ai_observer.observation import ObserverDirector
from companion_ai.conversation import ConversationService, ModelManager
from companion_ai.director import DirectorConfig, repetition
from companion_ai.event_deck import DeckSettings
from companion_ai.models import AIConfig
from tests.ai.test_character_cards import CARDS, MODELS
from tests.ai.test_event_deck_content import DEFINITION, play_only
from tests.fork.event_replay import Replay


class Audit(httpx.AsyncBaseTransport):
    def __init__(self):
        self.inner = httpx.AsyncHTTPTransport()
        self.calls = []

    async def handle_async_request(self, request):
        assert request.url.path in {'/api/show', '/api/ps', '/api/chat'}
        if request.url.path == '/api/chat':
            body = json.loads(request.content)
            assert body['think'] is False and not body.get('tools')
            self.calls.append(body)
        return await self.inner.handle_async_request(request)

    async def aclose(self):
        pass  # Provider clients share this pool; the harness closes it once.


async def run(args):
    if os.environ.get('EDGELOOP_LIVE_ACCEPTANCE') != '1':
        raise RuntimeError('Set EDGELOOP_LIVE_ACCEPTANCE=1 for real local inference')
    report = {'base': 'e2cd541', 'url': args.url, 'thinking': False,
              'hardware': 'none; Replay observations only', 'companions': [],
              'quality': 'Manual transcript review required; small stochastic sample.'}
    output = Path(args.output)
    audit = Audit()
    try:
        for identity, model in MODELS.items():
            r = Replay()
            r.state['devices'].update(toy_ready=True, handy=True, hr_ready=False, simulated_hr=False)
            r.state['safety'].update(fault='none', signal='missing')
            r.state.update(edges=0, seconds=0, status='RUNNING')
            r.step(None, seconds=0)
            manager = ModelManager(args.url, transport=audit)
            await manager.select(AIConfig(model=model, max_tokens=384))
            manager.current_summary = r.observation.summary
            frames = []
            director = ObserverDirector(DirectorConfig(), clock=r.clock.mono)
            s = ConversationService(r.observation, frames.append, manager,
                                    clock=r.clock.mono, director=director)
            s.deck_settings = DeckSettings(enabled=True, countdown_seconds=0)
            s.deck_definition = DEFINITION
            row = {'identity': identity, 'model': model, 'turns': []}
            report['companions'].append(row)
            user = 'What is your name? Please answer briefly.'
            assert s.request(user, user=True)['accepted']
            await s.task
            await asyncio.sleep(0)
            row['user_message'] = user
            row['user_reply'] = [f['text'] for f in frames if f['type'] == 'speech']
            previous = []
            for card in (c for c in CARDS if c.audience == identity):
                # Fresh replay observations advance past user grace and output time.
                for _ in range(90):
                    r.step(None, seconds=1)
                play_only(s, card.id)
                before, calls = len(frames), len(audit.calls)
                started = time.monotonic()
                s.pump()
                assert s.task is not None and not s.task.done(), s.director.last_reason
                await s.task
                await asyncio.sleep(0)
                visible = [f['text'] for f in frames[before:] if f['type'] == 'speech']
                text = '\n'.join(visible)
                item = {'card': card.id, 'brief': card.brief, 'text': text,
                        'seconds': round(time.monotonic() - started, 2),
                        'provider_calls': len(audit.calls) - calls,
                        'repetition': repetition(text, previous) if text else None,
                        'errors': [f for f in frames[before:] if f['type'] == 'conversation_error'],
                        'suppressed': [f for f in frames[before:] if f['type'] == 'response_suppressed']}
                row['turns'].append(item)
                if text:
                    previous.append(text)
                output.write_text(json.dumps(report, indent=2) + '\n')
                print(identity, card.id, repr(text), flush=True)
        report['provider_calls'] = len(audit.calls)
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n')
        await audit.inner.aclose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:11435')
    parser.add_argument('--output', default='/tmp/character-cards-smoke.json')
    asyncio.run(run(parser.parse_args()))
