# SPDX-License-Identifier: AGPL-3.0-only
"""Campaign progression: missions, verified objectives, rewards and saved progress.

The campaign never controls EdgeLoop. It reads the observer's canonical report after acceptance
(the same evidence the Session Journal uses) and decides, deterministically, whether a mission
objective is met. Model output is never evidence: nothing here reads chat or generated text.

Definitions live in config/campaigns/<campaign id>/campaign.json (rules) and narrative.json
(the scripted character lines). Progress is one JSON file in the observer's data directory.
See docs/fork/campaign/README.md.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import time
from typing import Literal
from pydantic import Field, ValidationError, model_validator
from .models import StrictModel

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = ROOT / 'config/campaigns'
PROGRESS_FILE = 'campaign-progress.json'
SCHEMA_VERSION = 1
Identifier = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_.-]*$')
Text = Field(min_length=1, max_length=600)
COUNTED = {'edge_count', 'orgasm_count'}
ObjectiveType = Literal['hr_monitor_connected', 'toy_connected', 'session_started', 'edge_count', 'orgasm_count',
                        'calibration_completed', 'calibration_saved']
# Reward types with an application mechanism today: companion unlocks (campaign roster), milestones and
# campaign completion. The others are recorded as earned so a later feature can honour them.
RewardType = Literal['unlock_companion', 'milestone', 'campaign_complete', 'story_branch', 'collectible', 'achievement']
EngineMode = Literal['classic', 'finisher', 'milker', 'shortener', 'headplay', 'ultimate', 'bratty', 'ruin', 'script',
                     'survival', 'oracle', 'edgetrain', 'calibrate']
SettingName = Literal['play_style', 'game', 'endgame', 'orgasm', 'intensity', 'pause', 'stop']
LIVE = {'RUNNING', 'PAUSED', 'RAMPDOWN'}


def now_iso(clock=time.time):
    return datetime.fromtimestamp(clock(), timezone.utc).isoformat(timespec='seconds')


class Objective(StrictModel):
    id: str = Identifier
    type: ObjectiveType
    label: str = Text
    count: int | None = Field(default=None, ge=1, le=1000)

    @model_validator(mode='after')
    def counted(self):
        if (self.type in COUNTED) != (self.count is not None):
            raise ValueError('count is required for edge_count/orgasm_count and not allowed otherwise')
        return self


class Reward(StrictModel):
    type: RewardType
    id: str = Identifier
    label: str = Text

    @property
    def key(self):
        return f'{self.type}:{self.id}'


class SessionRequirement(StrictModel):
    """The engine mode the mission session must start in, as the snapshot reports it."""
    active_mode: EngineMode | None = None
    label: str | None = Field(default=None, max_length=200)


class SettingsLimit(StrictModel):
    """AI Settings Control during the mission: only these changes may be requested."""
    allowed: list[SettingName] = Field(min_length=1, max_length=7)


class StoryMeta(StrictModel):
    chapter: int | None = Field(default=None, ge=1, le=1000)
    tags: list[str] = Field(default_factory=list, max_length=16)


class Mission(StrictModel):
    id: str = Identifier
    order: int = Field(ge=1, le=10000)
    title: str = Field(min_length=1, max_length=80)
    summary: str = Text
    companion: str = Identifier
    prerequisites: list[str] = Field(default_factory=list, max_length=16)
    objectives: list[Objective] = Field(min_length=1, max_length=12)
    rewards: list[Reward] = Field(default_factory=list, max_length=12)
    session: SessionRequirement | None = None
    settings_control: SettingsLimit | None = None
    replay: Literal['allowed', 'disabled'] = 'allowed'
    difficulty: Literal['introductory', 'standard', 'challenge'] | None = None
    optional: bool = False
    story: StoryMeta | None = None
    hints: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode='after')
    def unique_objectives(self):
        ids = [o.id for o in self.objectives]
        if len(ids) != len(set(ids)): raise ValueError('objective ids must be unique within a mission')
        return self


class Campaign(StrictModel):
    schema_version: Literal[1]
    id: str = Identifier
    order: int = Field(ge=1, le=10000)
    title: str = Field(min_length=1, max_length=80)
    description: str = Text
    artwork: str | None = Field(default=None, max_length=200, pattern=r'^[A-Za-z0-9_./-]+$')
    available_from_start: bool = True
    requires_campaigns: list[str] = Field(default_factory=list, max_length=8)
    starting_companions: list[str] = Field(default_factory=list, max_length=16)
    missions: list[Mission] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def consistent(self):
        ids = [m.id for m in self.missions]
        if len(ids) != len(set(ids)): raise ValueError('mission ids must be unique')
        known = set(ids)
        for m in self.missions:
            missing = [p for p in m.prerequisites if p not in known]
            if missing: raise ValueError(f'{m.id}: unknown prerequisite {missing[0]}')
        # Prerequisites must form a graph without cycles, so every mission is reachable.
        graph = {m.id: set(m.prerequisites) for m in self.missions}
        done = set()
        while graph:
            ready = [k for k, v in graph.items() if v <= done]
            if not ready: raise ValueError('mission prerequisites contain a cycle')
            for k in ready: done.add(k); graph.pop(k)
        unlocked = set(self.starting_companions) | {r.id for m in self.missions for r in m.rewards if r.type == 'unlock_companion'}
        for m in self.missions:
            if m.companion not in unlocked: raise ValueError(f'{m.id}: companion {m.companion} is never unlocked')
        return self

    def mission(self, mission_id):
        return next((m for m in self.missions if m.id == mission_id), None)


class NarrativeBlock(StrictModel):
    speaker: str = Identifier
    lines: list[str] = Field(min_length=1, max_length=12)


class MissionNarrative(StrictModel):
    briefing: NarrativeBlock
    completion: NarrativeBlock
    # Optional, for later: reactions to single objectives, and a short line for the Director/model.
    milestones: dict[str, NarrativeBlock] = Field(default_factory=dict, max_length=12)
    director_context: str | None = Field(default=None, max_length=400)


class Narrative(StrictModel):
    schema_version: Literal[1]
    campaign: str = Identifier
    status: Literal['draft', 'approved']
    missions: dict[str, MissionNarrative]
    campaign_complete: NarrativeBlock | None = None


class Book:
    """All campaigns found on disk. A broken campaign is left out and reported; the others still load."""

    def __init__(self, campaigns=(), narratives=None, errors=()):
        self.campaigns = sorted(campaigns, key=lambda c: (c.order, c.id))
        self.narratives = narratives or {}
        self.errors = list(errors)

    @classmethod
    def load(cls, directory=CAMPAIGN_DIR):
        campaigns, narratives, errors = [], {}, []
        for path in sorted(Path(directory).glob('*/campaign.json')) if Path(directory).is_dir() else []:
            try:
                campaign = Campaign.model_validate(json.loads(path.read_text()))
                if campaign.id != path.parent.name: raise ValueError('campaign id must match its folder name')
                if any(c.id == campaign.id for c in campaigns): raise ValueError('duplicate campaign id')
                narrative_path = path.parent / 'narrative.json'
                narrative = Narrative.model_validate(json.loads(narrative_path.read_text())) if narrative_path.exists() else None
                if narrative and narrative.campaign != campaign.id: raise ValueError('narrative belongs to another campaign')
                if narrative:
                    unknown = set(narrative.missions) - {m.id for m in campaign.missions}
                    if unknown: raise ValueError(f'narrative for unknown mission {sorted(unknown)[0]}')
                    for mid, block in narrative.missions.items():
                        objectives = {o.id for o in campaign.mission(mid).objectives}
                        if set(block.milestones) - objectives: raise ValueError(f'{mid}: milestone for an unknown objective')
                campaigns.append(campaign)
                if narrative: narratives[campaign.id] = narrative
            except (ValueError, OSError, ValidationError) as exc:
                detail = str(exc).splitlines()[0][:200] if not isinstance(exc, ValidationError) else f'{exc.error_count()} definition errors'
                errors.append({'path': path.parent.name, 'detail': detail})
                logger.warning('Campaign %s not loaded: %s', path.parent.name, detail)
        return cls(campaigns, narratives, errors)

    def campaign(self, campaign_id):
        return next((c for c in self.campaigns if c.id == campaign_id), None)


# ---- Saved progress -------------------------------------------------------------------------

class MissionRecord(StrictModel):
    completions: int = Field(ge=1, le=1000000)
    first_completed_at: str = Field(max_length=40)
    last_completed_at: str = Field(max_length=40)


class RewardRecord(StrictModel):
    earned_at: str = Field(max_length=40)
    mission: str = Field(max_length=64)


class CampaignRecord(StrictModel):
    missions: dict[str, MissionRecord] = Field(default_factory=dict)
    rewards: dict[str, RewardRecord] = Field(default_factory=dict)
    completed_at: str | None = Field(default=None, max_length=40)
    # Facts a mission confirmed and the campaign keeps, e.g. the calibrated maximum heart rate.
    records: dict[str, int | str | None] = Field(default_factory=dict, max_length=32)


class ActiveMission(StrictModel):
    campaign: str = Field(max_length=64)
    mission: str = Field(max_length=64)
    started_at: str = Field(max_length=40)


class Progress(StrictModel):
    schema_version: Literal[1]
    campaigns: dict[str, CampaignRecord] = Field(default_factory=dict)
    active: ActiveMission | None = None


# Each entry upgrades a saved file by one version: MIGRATIONS[1] turns version 1 into version 2.
# A file from a newer app (higher version) is never rewritten; the campaign stays off instead.
MIGRATIONS = {}


def migrate(data):
    if not isinstance(data, dict) or not isinstance(data.get('schema_version'), int) or isinstance(data.get('schema_version'), bool):
        raise ValueError('Unsupported campaign progress format')
    version = data['schema_version']
    if version > SCHEMA_VERSION: raise ValueError('Campaign progress was saved by a newer EdgeLoop AI')
    while version < SCHEMA_VERSION:
        if version not in MIGRATIONS: raise ValueError(f'No migration from campaign progress version {version}')
        data = MIGRATIONS[version](deepcopy(data)); version = data['schema_version']
    return data


# ---- Evidence from the canonical report ------------------------------------------------------

def real_hr(report):
    """A heart-rate monitor the participant connected: ready, over Bluetooth, and not the built-in simulator."""
    d = (report or {}).get('devices') or {}
    return bool(d.get('hr_ready') and d.get('ble') and not d.get('simulated_hr'))


def toy_ready(report):
    return bool(((report or {}).get('devices') or {}).get('toy_ready'))


def details(report):
    return (report or {}).get('details') or {}


class Attempt:
    """One try at the active mission. Counts restart when the mission session ends before completion."""

    def __init__(self, mission):
        self.mission = mission
        self.session_id = None
        self.done = {}
        self.edges = self.orgasms = 0
        self.last_edges = self.last_orgasms = None
        self.reported = False
        self.metric = None
        self.completed = False
        self.reset_reason = None

    def view(self, report=None, companion_ok=False):
        live = {'hr_monitor_connected': real_hr(report), 'toy_connected': toy_ready(report)}
        items = []
        for o in self.mission.objectives:
            done = bool(self.done.get(o.id)) or (self.session_id is None and live.get(o.type, False))
            item = {'id': o.id, 'type': o.type, 'label': o.label, 'done': done}
            if o.type == 'edge_count': item.update(progress=min(self.edges, o.count), count=o.count)
            if o.type == 'orgasm_count': item.update(progress=min(self.orgasms, o.count), count=o.count)
            items.append(item)
        return {'session_id': self.session_id, 'objectives': items, 'companion_selected': companion_ok,
                'completed': self.completed, 'reset_reason': self.reset_reason}


class CampaignService:
    """Owns the campaign definitions, the saved progress and the in-memory attempt."""

    def __init__(self, store, book=None, identity=None, clock=time.time):
        self.store, self.clock = store, clock
        self.book = book if book is not None else Book.load()
        self.identity = identity or (lambda model: None)
        self.attempt = None
        self.error = None
        self.notice = None
        try:
            raw = store.read(PROGRESS_FILE, None)
            self.progress = Progress.model_validate(migrate(raw)) if raw is not None else Progress(schema_version=SCHEMA_VERSION)
        except (ValueError, OSError, ValidationError):
            self.progress = Progress(schema_version=SCHEMA_VERSION)
            self.error = 'Campaign progress could not be read. The file was left as it is and the campaign is unavailable; Freeplay is not affected.'
        active = self.progress.active
        if active and not self._mission(active.campaign, active.mission):
            self.progress.active = None  # Its definition is gone (content removed); nothing else changes.
        if self.progress.active:
            self.attempt = Attempt(self._mission(self.progress.active.campaign, self.progress.active.mission))

    # -- lookups
    def _mission(self, campaign_id, mission_id):
        campaign = self.book.campaign(campaign_id)
        return campaign.mission(mission_id) if campaign else None

    def record(self, campaign_id):
        return self.progress.campaigns.get(campaign_id) or CampaignRecord()

    def companion_unlocked(self, campaign, companion):
        return companion in campaign.starting_companions or f'unlock_companion:{companion}' in self.record(campaign.id).rewards

    def campaign_available(self, campaign):
        if campaign.available_from_start: return True
        return all(self.record(c).completed_at for c in campaign.requires_campaigns)

    def mission_state(self, campaign, mission):
        active = self.progress.active
        if active and active.campaign == campaign.id and active.mission == mission.id: return 'active'
        record = self.record(campaign.id)
        if mission.id in record.missions: return 'completed'
        if not self.campaign_available(campaign): return 'locked'
        if all(p in record.missions for p in mission.prerequisites) and self.companion_unlocked(campaign, mission.companion):
            return 'available'
        return 'locked'

    def allowed_settings(self):
        """AI Settings Control limit while a mission with one is active; None means unrestricted."""
        if not self.attempt or self.attempt.completed or not self.attempt.mission.settings_control: return None
        return frozenset(self.attempt.mission.settings_control.allowed)

    # -- views
    def state(self, report=None, model=None):
        campaigns = []
        for c in self.book.campaigns:
            record = self.record(c.id)
            narrative = self.book.narratives.get(c.id)
            missions = []
            for m in sorted(c.missions, key=lambda m: (m.order, m.id)):
                block = narrative.missions.get(m.id) if narrative else None
                missions.append({'id': m.id, 'order': m.order, 'title': m.title, 'summary': m.summary, 'companion': m.companion,
                    'state': self.mission_state(c, m), 'prerequisites': m.prerequisites, 'optional': m.optional,
                    'objectives': [o.model_dump(exclude_none=True) for o in m.objectives],
                    'rewards': [{'type': r.type, 'id': r.id, 'label': r.label, 'earned': r.key in record.rewards} for r in m.rewards],
                    'session': m.session.model_dump(exclude_none=True) if m.session else None,
                    'settings_control': m.settings_control.model_dump() if m.settings_control else None,
                    'replay': m.replay, 'difficulty': m.difficulty, 'hints': m.hints,
                    'completions': record.missions[m.id].completions if m.id in record.missions else 0,
                    'briefing': block.briefing.model_dump() if block else None})
            done = sum(1 for m in c.missions if m.id in record.missions and not m.optional)
            total = sum(1 for m in c.missions if not m.optional)
            campaigns.append({'id': c.id, 'title': c.title, 'description': c.description, 'artwork': c.artwork,
                'available': self.campaign_available(c), 'completed': bool(record.completed_at), 'completed_at': record.completed_at,
                'progress': {'completed': done, 'total': total}, 'companions': sorted(
                    {m.companion for m in c.missions if self.companion_unlocked(c, m.companion)}),
                'narrative_status': narrative.status if narrative else None, 'records': dict(record.records), 'missions': missions})
        active = self.progress.active.model_dump() if self.progress.active else None
        attempt = None
        if self.attempt:
            attempt = self.attempt.view(report, bool(model) and self.identity(model) == self.attempt.mission.companion)
        return {'type': 'campaign_state', 'campaigns': campaigns, 'active': active, 'attempt': attempt,
                'error': self.error, 'notice': self.notice, 'definition_errors': self.book.errors}

    # -- commands
    def _save(self, progress):
        if self.error: raise ValueError(self.error)
        self.store.write(PROGRESS_FILE, progress.model_dump(mode='json'))
        self.progress = progress

    def start(self, campaign_id, mission_id, report=None):
        campaign = self.book.campaign(campaign_id)
        mission = campaign.mission(mission_id) if campaign else None
        if not mission: raise ValueError('Unknown mission.')
        if report and report.get('status') in LIVE: raise ValueError('Stop the current session before starting a mission.')
        state = self.mission_state(campaign, mission)
        if state == 'locked': raise ValueError('This mission is still locked.')
        if state == 'completed' and mission.replay != 'allowed': raise ValueError('This mission cannot be replayed.')
        progress = self.progress.model_copy(deep=True)
        progress.active = ActiveMission(campaign=campaign.id, mission=mission.id, started_at=now_iso(self.clock))
        self._save(progress)
        self.attempt = Attempt(mission)
        self.notice = None

    def abandon(self):
        progress = self.progress.model_copy(deep=True)
        progress.active = None
        self._save(progress)
        self.attempt = None

    # -- evidence
    def observe(self, report, events, model):
        """Called after the observer accepted an observation. Returns messages to publish (state changes, results)."""
        if self.error or not self.attempt or self.attempt.completed or not report: return []
        attempt, mission = self.attempt, self.attempt.mission
        before = json.dumps(attempt.view(report, False), sort_keys=True)
        companion_ok = self.identity(model) == mission.companion
        sid, status, d = report.get('session_id'), report.get('status'), details(report)
        kinds = {e for e in events}
        out = []
        if attempt.session_id and sid != attempt.session_id:
            self._reset(attempt, 'session_changed')
        # Adopt the mission session: running, with the mission's companion, a real heart-rate monitor, a toy
        # and the required engine mode. Each condition is the engine's own reported state.
        if attempt.session_id is None and status == 'RUNNING' and companion_ok:
            mode_ok = not mission.session or not mission.session.active_mode or report.get('active_mode') == mission.session.active_mode
            if real_hr(report) and toy_ready(report) and mode_ok:
                attempt.session_id = sid
                attempt.last_edges, attempt.last_orgasms = report.get('edges', 0), d.get('orgasm_count') or 0
                attempt.reported = bool(d.get('completion_reported'))
                attempt.reset_reason = None
                for o in mission.objectives:
                    if o.type in {'hr_monitor_connected', 'toy_connected', 'session_started'}: attempt.done[o.id] = True
        if attempt.session_id == sid and attempt.session_id is not None:
            edges, orgasms = report.get('edges', 0), d.get('orgasm_count') or 0
            # Counters only grow inside a session; an IDLE reset to 0 must not count backwards or double.
            counted = max(0, orgasms - attempt.last_orgasms)
            # Survival's Finished me and Came Early report an orgasm without raising orgasm_count; each counts once.
            if not counted and (d.get('completion_reported') and not attempt.reported or 'came_early' in kinds): counted = 1
            attempt.reported = attempt.reported or bool(d.get('completion_reported'))
            if companion_ok:
                attempt.edges += max(0, edges - attempt.last_edges)
                attempt.orgasms += counted
            attempt.last_edges, attempt.last_orgasms = max(attempt.last_edges, edges), max(attempt.last_orgasms, orgasms)
            calibrated = d.get('terminal_outcome') == 'calibration_completed' or 'completion_accepted' in kinds
            for o in mission.objectives:
                if o.type == 'edge_count' and attempt.edges >= o.count: attempt.done[o.id] = True
                if o.type == 'orgasm_count' and attempt.orgasms >= o.count: attempt.done[o.id] = True
                if o.type == 'calibration_completed' and calibrated and companion_ok: attempt.done[o.id] = True
                if o.type == 'calibration_saved' and calibrated and companion_ok and d.get('calibration_saved') is True:
                    metric = d.get('dual_max_bpm') if d.get('calibration_pass') == 'dual' else d.get('single_max_bpm')
                    if isinstance(metric, int):
                        attempt.done[o.id] = True
                        attempt.metric = {'calibration_pass': d.get('calibration_pass'), 'max_bpm': metric}
            if all(attempt.done.get(o.id) for o in mission.objectives):
                result = self._complete(attempt)
                if result: out.append(result)
            elif status == 'IDLE':
                # The session ended before the mission was done: the next session starts the counts again.
                self._reset(attempt, 'session_ended')
        if json.dumps(attempt.view(report, False), sort_keys=True) != before or out:
            out.insert(0, self.state(report, model))
        return out

    def _reset(self, attempt, reason):
        attempt.session_id = None; attempt.done = {}; attempt.edges = attempt.orgasms = 0
        attempt.last_edges = attempt.last_orgasms = None; attempt.reported = False; attempt.metric = None; attempt.reset_reason = reason

    def _complete(self, attempt):
        """Persist first, then announce. A failed write announces nothing and retries on the next observation."""
        active = self.progress.active
        campaign = self.book.campaign(active.campaign)
        mission = attempt.mission
        progress = self.progress.model_copy(deep=True)
        record = progress.campaigns.setdefault(campaign.id, CampaignRecord())
        stamp = now_iso(self.clock)
        replay = mission.id in record.missions
        if replay:
            entry = record.missions[mission.id]
            entry.completions += 1; entry.last_completed_at = stamp
        else:
            record.missions[mission.id] = MissionRecord(completions=1, first_completed_at=stamp, last_completed_at=stamp)
        earned = []
        for reward in mission.rewards:
            if reward.key in record.rewards: continue  # Idempotent: a replay or a retry never grants twice.
            record.rewards[reward.key] = RewardRecord(earned_at=stamp, mission=mission.id)
            earned.append({'type': reward.type, 'id': reward.id, 'label': reward.label})
        if attempt.metric:
            record.records['calibration_pass'] = attempt.metric['calibration_pass']
            record.records['calibrated_max_bpm'] = attempt.metric['max_bpm']
        campaign_done = any(r.type == 'campaign_complete' for r in mission.rewards) and record.completed_at is None
        if campaign_done: record.completed_at = stamp
        progress.active = None
        open_before = {m.id for m in campaign.missions if self.mission_state(campaign, m) in {'available', 'completed', 'active'}}
        try:
            self._save(progress)
        except (ValueError, OSError):
            self.notice = 'Mission complete, but progress could not be saved. Check free disk space; it will be saved on the next update.'
            logger.warning('Campaign progress could not be saved')
            return None
        attempt.completed = True
        self.notice = None
        narrative = self.book.narratives.get(campaign.id)
        block = narrative.missions.get(mission.id) if narrative else None
        newly = [m.id for m in campaign.missions if m.id not in open_before and self.mission_state(campaign, m) == 'available']
        result = {'type': 'mission_result', 'campaign': campaign.id, 'mission': mission.id, 'title': mission.title,
                  'companion': mission.companion, 'replay': replay, 'earned': earned, 'unlocked_missions': newly,
                  'objectives': attempt.view(None, True)['objectives'], 'records': dict(record.records),
                  'completion': block.completion.model_dump() if block else None,
                  'campaign_complete': bool(campaign_done),
                  'campaign_completion': narrative.campaign_complete.model_dump() if campaign_done and narrative and narrative.campaign_complete else None}
        self.attempt = None
        return result
