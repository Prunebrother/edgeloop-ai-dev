# SPDX-License-Identifier: AGPL-3.0-only
"""Shared defaults and saved-setting precedence; no inference or hardware."""
from pathlib import Path
import re
import pytest
from ai_observer.server import create_app
from companion_ai.director import DirectorConfig
from companion_ai.event_intelligence import EventConfig
from companion_ai.models import AIConfig
from companion_ai.storage import SettingsStore
from tests.fork.test_observer import TOKEN

MODELS=[f'{name}-narrative-v1:latest' for name in ('nova','evelyn','daisy','celeste')]
EXPECTED={
 'spontaneous_enabled':True,'experimental_idle_enabled':True,
 'idle_interval_seconds':20.,'idle_response_cooldown_seconds':15.,
 'reaction_interval_seconds':4.,'topic_cooldown_seconds':60.,'max_consecutive_unsolicited':50,
}

def select(app,model):
 app.state.speech.adapter.config=AIConfig(model=model)
 app.state.speech.activate_model()
 return app.state.speech.character_state()['director']['settings']

def assert_defaults(settings):
 assert {key:settings[key] for key in EXPECTED}==EXPECTED

@pytest.mark.parametrize('model',MODELS)
def test_new_companion_uses_shared_director_and_event_defaults(tmp_path,model):
 app=create_app(TOKEN,tmp_path)
 assert_defaults(select(app,model))
 assert app.state.speech.event_intelligence.config.enabled
 assert not (tmp_path/'director-models.json').exists()

@pytest.mark.parametrize('model',MODELS)
def test_saved_model_override_survives_restart_and_other_companions_inherit_defaults(tmp_path,model):
 app=create_app(TOKEN,tmp_path);select(app,model)
 overrides={'spontaneous_enabled':False,'experimental_idle_enabled':False,'idle_interval_seconds':90.,'max_consecutive_unsolicited':3}
 app.state.speech.configure_director(overrides,model)
 path=tmp_path/'director-models.json';saved=path.read_bytes()
 restored=create_app(TOKEN,tmp_path)
 for candidate in MODELS:
  settings=select(restored,candidate)
  expected=EXPECTED|overrides if candidate==model else EXPECTED
  assert {key:settings[key] for key in EXPECTED}==expected
 assert path.read_bytes()==saved


def test_saved_global_and_event_settings_are_not_rewritten(tmp_path):
 store=SettingsStore(tmp_path)
 store.write('director.json',{'experimental_idle_enabled':False,'idle_interval_seconds':75.})
 store.write('event-intelligence.json',EventConfig(enabled=False).model_dump())
 before={name:(tmp_path/name).read_bytes() for name in ('director.json','event-intelligence.json')}
 app=create_app(TOKEN,tmp_path)
 for model in MODELS:
  settings=select(app,model)
  assert not settings['experimental_idle_enabled'] and settings['idle_interval_seconds']==75.
  assert settings['max_consecutive_unsolicited']==50
 assert not app.state.speech.event_intelligence.config.enabled
 assert all((tmp_path/name).read_bytes()==contents for name,contents in before.items())


def test_frontend_initial_fields_match_backend_defaults():
 root=Path(__file__).resolve().parents[2]
 menu=(root/'src/js/ai/character-menus.js').read_text()
 defaults=DirectorConfig()
 for key in ('idle_interval_seconds','idle_response_cooldown_seconds','reaction_interval_seconds','topic_cooldown_seconds','max_consecutive_unsolicited'):
  match=re.search(r'data-director-field="'+key+r'"[^>]*value="([^"]+)"',menu)
  assert match and float(match[1])==getattr(defaults,key),key
 for attribute in ('data-proactive','data-idle-enabled'):
  tag=re.search(r'<input\b[^>]*\b'+attribute+r'\b[^>]*>',menu)
  assert tag and re.search(r'\bchecked\b',tag[0]),attribute
 events=(root/'src/js/ai/event-settings.js').read_text()
 tag=re.search(r'<input\b[^>]*\bdata-events-enabled\b[^>]*>',events)
 assert EventConfig().enabled and tag and re.search(r'\bchecked\b',tag[0])
 assert 'Opt-in;' not in menu and '40–60 second' not in menu
