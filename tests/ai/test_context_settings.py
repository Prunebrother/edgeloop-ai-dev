# SPDX-License-Identifier: AGPL-3.0-only
from fastapi.testclient import TestClient
from ai_observer.server import create_app
from companion_ai.context_compiler import ContextConfig
from tests.ai.test_f25 import runtime
from tests.fork.test_observer import TOKEN,ORIGIN,auth,until


def test_persistent_backend_budgets_and_explicit_fallback_never_generate(tmp_path):
 wire=[];app=create_app(TOKEN,tmp_path,transport=runtime(wire))
 with TestClient(app) as client:
  with client.websocket_connect('/observe',headers={'Origin':ORIGIN}) as ws:
   auth(ws);cfg=ContextConfig(enabled=False,history_tokens=500).model_dump()
   ws.send_json({'version':1,'type':'configure_context','config':cfg})
   until(ws,'character_state')
   assert app.state.models.context_config.enabled is False and not wire
   cfg['history_tokens']=-1
   ws.send_json({'version':1,'type':'configure_context','config':cfg});until(ws,'protocol_error')
   assert app.state.models.context_config.history_tokens==500
 restored=create_app(TOKEN,tmp_path,transport=runtime(wire))
 assert not restored.state.models.context_config.enabled
 assert restored.state.models.config.thinking is False
