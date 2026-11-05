# SPDX-License-Identifier: AGPL-3.0-only
"""Upstream-integration guards: snapshot/protocol stay in step with the engine's
modes, the observer protocol carries no commands, and the local server never
exposes an agent or relay endpoint."""
import re
import typing
from pathlib import Path

from ai_observer import protocol
from tools.serve_local import public_file

ROOT = Path(__file__).resolve().parents[2]


def js_list(source: str, name: str) -> list[str]:
    match = re.search(rf'{name}\s*=\s*\[([^\]]*)\]', source)
    assert match, f'{name} not found'
    return re.findall(r"'([^']+)'", match.group(1))


def literal(annotation) -> list[str]:
    return list(typing.get_args(annotation))


ENGINE = (ROOT / 'src/js/engine.js').read_text()
SNAPSHOT = (ROOT / 'src/js/ai/snapshot.js').read_text()
TEASE = js_list(ENGINE, 'export const TEASE_MODES')
GAMES = js_list(ENGINE, 'export const GAME_MODES')


def test_snapshot_and_protocol_accept_every_engine_play_style():
    # A play style the observer does not know makes the projection fail closed,
    # which silently blinds the companion for that session.
    assert sorted(js_list(SNAPSHOT, 'const modes')) == sorted(TEASE)
    assert sorted(literal(protocol.Mode)) == sorted(TEASE)
    active = literal(protocol.Snapshot.model_fields['active_mode'].annotation)
    assert set(TEASE) | set(GAMES) <= set(active)


def test_snapshot_and_protocol_accept_every_engine_goal():
    goals = js_list(SNAPSHOT, 'const goals')
    assert set(GAMES) | {'tease', 'nnn'} <= set(goals)
    assert sorted(literal(protocol.Goal)) == sorted(goals)


COMMANDS = {'SESSION_STATE', 'SESSION_RESET', 'MODE_CHANGE', 'ENDGAME', 'DURATION', 'INTENSITY',
            'SPEED_WINDOW', 'ORGASM_TOGGLE', 'EDGE_MARK', 'MANUAL_PATTERN', 'MANUAL_LEVEL'}


def test_observer_protocol_is_closed_and_has_no_engine_commands():
    schema = protocol.Messages.json_schema()
    types = set()

    def walk(node):
        if isinstance(node, dict):
            if 'type' in node.get('properties', {}):
                const = node['properties']['type'].get('const')
                if const: types.add(const)
            for child in node.values(): walk(child)
        elif isinstance(node, list):
            for child in node: walk(child)
    walk(schema)
    assert types == {'observation', 'select_model', 'chat', 'list_models', 'cancel_generation',
                     'reset_narrative', 'get_character_state', 'configure_director', 'configure_events',
                     'conversation_activity', 'configure_context', 'update_objective', 'session_journal',
                     'configure_curator'}
    assert not types & COMMANDS


def test_observer_server_never_emits_engine_commands():
    server = (ROOT / 'ai_observer/server.py').read_text()
    emitted = set(re.findall(r"'type':'([A-Za-z_]+)'", server))
    assert emitted and not emitted & COMMANDS


def test_local_server_exposes_no_agent_relay_or_worker_paths(tmp_path):
    for raw in ['/api/agent/abcdefghijklmnopqrstuv', '/api/agent', '/api/room/peer', '/worker/index.js',
                '/tools/edgeloop_openwebui.py', '/wrangler.jsonc', '/app/host.mjs', '/ai_observer/server.py']:
        assert public_file(raw) is None, raw
