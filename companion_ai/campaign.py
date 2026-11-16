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
SCHEMA_VERSION = 2
Identifier = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_.-]*$')
Text = Field(min_length=1, max_length=600)
COUNTED = {'edge_count', 'orgasm_count'}
ObjectiveType = Literal['hr_monitor_connected', 'toy_connected', 'session_started', 'edge_count', 'orgasm_count',
                        'calibration_completed', 'calibration_saved', 'style_stages', 'stage_sequence']
# The engine's play styles (snapshot `experience`), the configurations a style_stages objective can tell apart.
PLAY_STYLES = ('classic', 'finisher', 'milker', 'shortener', 'headplay', 'ultimate', 'bratty', 'ruin')
StyleName = Literal['classic', 'finisher', 'milker', 'shortener', 'headplay', 'ultimate', 'bratty', 'ruin']
# As the play-style cards in EdgeLoop name them.
STYLE_WORDS = {'classic': 'Simple Ramp', 'finisher': 'Finisher', 'milker': 'Prostate Milker', 'shortener': 'Glans Protector',
               'headplay': 'Head Play', 'ultimate': 'Ultimate Milker', 'bratty': 'Bratty Tease', 'ruin': 'Ruin & Leak'}
# At most this many seconds of running time are credited between two observations (they arrive about every second);
# a longer gap, such as a reconnect, is not counted, since what happened in it is unknown.
MAX_STEP_SECONDS = 5
# Reward types with an application mechanism today: companion unlocks (campaign roster), milestones and
# campaign completion. The others are recorded as earned so a later feature can honour them.
RewardType = Literal['unlock_companion', 'milestone', 'chapter_complete', 'campaign_complete', 'story_branch', 'collectible', 'achievement']
# Rewards that mark completion: they follow from the completed missions and current definitions (recomputed on load).
COMPLETION_REWARDS = {'chapter_complete', 'campaign_complete'}
EngineMode = Literal['classic', 'finisher', 'milker', 'shortener', 'headplay', 'ultimate', 'bratty', 'ruin', 'script',
                     'survival', 'oracle', 'edgetrain', 'calibrate']
SettingName = Literal['play_style', 'game', 'endgame', 'orgasm', 'intensity', 'pause', 'stop']
LIVE = {'RUNNING', 'PAUSED', 'RAMPDOWN'}
MISSING = object()
# Objectives that are story moments when reached; the setup items before a session are not.
GOAL_TYPES = {'edge_count', 'orgasm_count', 'calibration_completed', 'calibration_saved', 'style_stages', 'stage_sequence'}
COMPANION_ALIASES = {'evelyn': ('Voss',), 'daisy': ('Harper', 'Cloverfield'), 'celeste': ('IRRA',)}
MODE_WORDS = {'calibrate': 'Calibration', 'edgetrain': 'Edge Training'}


def now_iso(clock=time.time):
    return datetime.fromtimestamp(clock(), timezone.utc).isoformat(timespec='seconds')


class Stage(StrictModel):
    """One step of a stage_sequence: active running time at a fixed engine intensity (snapshot %, 50-150)."""
    id: str = Identifier
    label: str = Field(min_length=1, max_length=80)
    seconds: int = Field(ge=10, le=7200)
    intensity: int = Field(ge=50, le=150)


class Objective(StrictModel):
    """Composable objectives, all decided from the engine's canonical report:
    - edge_count / orgasm_count: `count` events in the mission session, optional `milestones` thresholds,
      optional `after` (count only once that objective is met).
    - style_stages: `count` different play styles, each run for `seconds` of active time with no game on.
    - stage_sequence: `stages` in order, each `seconds` of active time at its intensity (within `tolerance`)."""
    id: str = Identifier
    type: ObjectiveType
    label: str = Text
    count: int | None = Field(default=None, ge=1, le=1000)
    milestones: list[int] = Field(default_factory=list, max_length=10)
    after: str | None = Field(default=None, max_length=64)
    seconds: int | None = Field(default=None, ge=10, le=7200)
    styles: list[StyleName] = Field(default_factory=lambda: list(PLAY_STYLES), min_length=1, max_length=8)
    stages: list[Stage] = Field(default_factory=list, max_length=8)
    tolerance: int = Field(default=2, ge=0, le=10)

    @model_validator(mode='after')
    def counted(self):
        if (self.type in COUNTED | {'style_stages'}) != (self.count is not None):
            raise ValueError('count is required for edge_count, orgasm_count and style_stages, and not allowed otherwise')
        if (self.type == 'style_stages') != (self.seconds is not None):
            raise ValueError('seconds is required for style_stages and not allowed otherwise')
        if (self.type == 'stage_sequence') != bool(self.stages):
            raise ValueError('stages are required for stage_sequence and not allowed otherwise')
        if self.milestones and (self.type not in COUNTED or any(not 0 < n < self.count for n in self.milestones) or sorted(set(self.milestones)) != self.milestones):
            raise ValueError('milestones are increasing counts below the target, on edge_count/orgasm_count only')
        if self.after and self.type not in COUNTED: raise ValueError('after is for edge_count/orgasm_count only')
        if self.type == 'style_stages' and self.count > len(self.styles): raise ValueError('more stages than styles')
        if len({s.id for s in self.stages}) != len(self.stages): raise ValueError('stage ids must be unique')
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
    """AI Settings Control during the mission: only these changes may be requested. Once the objective named in
    `after` is met, `then_allowed` applies instead (Mission 9: Force Orgasm only in the final phase)."""
    allowed: list[SettingName] = Field(min_length=1, max_length=7)
    after: str | None = Field(default=None, max_length=64)
    then_allowed: list[SettingName] | None = Field(default=None, min_length=1, max_length=7)

    @model_validator(mode='after')
    def paired(self):
        if (self.after is None) != (self.then_allowed is None): raise ValueError('after and then_allowed go together')
        return self


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
    # Earlier missions whose saved results this mission's companion is told about (Mission 9's review).
    review: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode='after')
    def unique_objectives(self):
        ids = [o.id for o in self.objectives]
        if len(ids) != len(set(ids)): raise ValueError('objective ids must be unique within a mission')
        for i, o in enumerate(self.objectives):
            if o.after and o.after not in ids[:i]: raise ValueError(f'{o.id}: after must name an earlier objective')
        if self.settings_control and self.settings_control.after and self.settings_control.after not in ids:
            raise ValueError('settings_control.after must name an objective')
        return self


class Chapter(StrictModel):
    """Missions belong to a chapter through story.chapter (its number). A chapter is complete when the
    chapter_complete reward with its id is earned; it opens when the missions' prerequisites allow."""
    number: int = Field(ge=1, le=1000)
    id: str = Identifier
    title: str = Field(min_length=1, max_length=80)
    summary: str = Text


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
    chapters: list[Chapter] = Field(default_factory=list, max_length=50)
    missions: list[Mission] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def consistent(self):
        ids = [m.id for m in self.missions]
        if len(ids) != len(set(ids)): raise ValueError('mission ids must be unique')
        known = set(ids)
        for m in self.missions:
            missing = [p for p in m.prerequisites if p not in known]
            if missing: raise ValueError(f'{m.id}: unknown prerequisite {missing[0]}')
            if set(m.review) - known: raise ValueError(f'{m.id}: review names an unknown mission')
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
        if self.chapters:
            numbers = {c.number for c in self.chapters}
            if len(numbers) != len(self.chapters) or len({c.id for c in self.chapters}) != len(self.chapters): raise ValueError('chapter numbers and ids must be unique')
            for m in self.missions:
                if not m.story or m.story.chapter not in numbers: raise ValueError(f'{m.id}: story.chapter must name a chapter')
            ends = {r.id for m in self.missions for r in m.rewards if r.type == 'chapter_complete'}
            if ends - {c.id for c in self.chapters}: raise ValueError('chapter_complete for an unknown chapter')
        return self

    def chapter_of(self, mission):
        number = mission.story.chapter if mission.story else None
        return next((c for c in self.chapters if c.number == number), None)

    def mission(self, mission_id):
        return next((m for m in self.missions if m.id == mission_id), None)


class NarrativeBlock(StrictModel):
    speaker: str = Identifier
    lines: list[str] = Field(min_length=1, max_length=20)
    # A block can be a draft inside an approved narrative (new text awaiting the author's review).
    status: Literal['draft', 'approved'] | None = None


class MissionNarrative(StrictModel):
    briefing: NarrativeBlock
    completion: NarrativeBlock
    # Scripted lines for progress moments, keyed "<objective id>:<moment>": a count ("edges:5"), a completed
    # play-style stage ("styles:stage1"), a stage of a sequence ("assessment:baseline"), or "start" when the
    # mission session begins. Shown in the conversation; the model is not asked to speak for them.
    milestones: dict[str, NarrativeBlock] = Field(default_factory=dict, max_length=24)
    director_context: str | None = Field(default=None, max_length=400)

    def draft(self):
        return any(b.status == 'draft' for b in (self.briefing, self.completion, *self.milestones.values()))


class Narrative(StrictModel):
    schema_version: Literal[1]
    campaign: str = Identifier
    status: Literal['draft', 'approved']
    missions: dict[str, MissionNarrative]
    chapters: dict[str, NarrativeBlock] = Field(default_factory=dict, max_length=50)
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
                        if {k.split(':', 1)[0] for k in block.milestones} - objectives - {'start'}: raise ValueError(f'{mid}: milestone for an unknown objective')
                    if set(narrative.chapters) - {c.id for c in campaign.chapters}: raise ValueError('narrative for an unknown chapter')
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


class ChapterRecord(StrictModel):
    completed_at: str = Field(max_length=40)


class CampaignRecord(StrictModel):
    missions: dict[str, MissionRecord] = Field(default_factory=dict)
    rewards: dict[str, RewardRecord] = Field(default_factory=dict)
    chapters: dict[str, ChapterRecord] = Field(default_factory=dict)
    completed_at: str | None = Field(default=None, max_length=40)
    # Facts a mission confirmed and the campaign keeps, e.g. the calibrated maximum heart rate.
    records: dict[str, int | str | None] = Field(default_factory=dict, max_length=32)


class ActiveMission(StrictModel):
    campaign: str = Field(max_length=64)
    mission: str = Field(max_length=64)
    started_at: str = Field(max_length=40)


class Progress(StrictModel):
    schema_version: Literal[2]
    campaigns: dict[str, CampaignRecord] = Field(default_factory=dict)
    active: ActiveMission | None = None


# Each entry upgrades a saved file by one version: MIGRATIONS[1] turns version 1 into version 2.
# A file from a newer app (higher version) is never rewritten; the campaign stays off instead.
def _v1_to_v2(data):
    """Version 2 adds chapters. Completion markers (campaign completed_at, completion rewards) are dropped here and
    recomputed from the completed missions under the current definitions when progress is loaded, so a campaign
    completed at Mission 5 under version 1 becomes 'Chapter 1 complete' once Chapter 2 exists."""
    for record in (data.get('campaigns') or {}).values():
        if not isinstance(record, dict): continue
        record['completed_at'] = None
        rewards = record.get('rewards')
        if isinstance(rewards, dict):
            record['rewards'] = {k: v for k, v in rewards.items() if not (isinstance(k, str) and k.split(':', 1)[0] in COMPLETION_REWARDS)}
        record.setdefault('chapters', {})
    data['schema_version'] = 2
    return data


MIGRATIONS = {1: _v1_to_v2}


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
        # Per counted objective (an `after` objective counts only once its predecessor is met).
        self.counts = {}
        # Active running seconds: per play style (style_stages) and per stage id (stage_sequence).
        self.style_time = {}
        self.stage_time = {}
        # The last observation's time and configuration, so an interval is credited only when both ends agree.
        self.last_seconds = None
        self.last_config = None
        # Play styles that filled a stage, in the order they did, per style_stages objective.
        self.filled = {}
        # Scripted progress moments already shown in this try.
        self.marked = set()
        self.metric = None
        self.completed = False
        self.reset_reason = None
        self.cued = set()
        # All objectives met but not yet saved: kept until the save succeeds, whatever the next report says.
        self.pending = False
        # Bumped on every reset, so a cue from an earlier try is recognised as stale.
        self.generation = 0

    def done_styles(self, o):
        """Play styles that filled a stage, in the order they did."""
        return list(self.filled.get(o.id, ()))

    def current_stage(self, o):
        return next((st for st in o.stages if self.stage_time.get(st.id, 0) < st.seconds), None)

    def view(self, report=None, companion_ok=False):
        live = {'hr_monitor_connected': real_hr(report), 'toy_connected': toy_ready(report)}
        items = []
        for o in self.mission.objectives:
            done = bool(self.done.get(o.id)) or (self.session_id is None and live.get(o.type, False))
            item = {'id': o.id, 'type': o.type, 'label': o.label, 'done': done}
            if o.type in COUNTED:
                item.update(progress=min(self.counts.get(o.id, 0), o.count), count=o.count)
                if o.milestones: item['milestones'] = list(o.milestones)
                if o.after: item['after'] = o.after
            if o.type == 'style_stages':
                filled = self.done_styles(o)
                current = (report or {}).get('experience') if self.session_id else None
                stages = [{'style': k, 'label': STYLE_WORDS.get(k, k), 'seconds': min(self.style_time[k], o.seconds), 'done': True} for k in filled]
                if current in o.styles and current not in filled and len(filled) < o.count:
                    stages.append({'style': current, 'label': STYLE_WORDS.get(current, current), 'seconds': self.style_time.get(current, 0), 'done': False, 'current': True})
                item.update(progress=len(filled), count=o.count, stage_seconds=o.seconds, stages=stages,
                            elapsed=sum(min(v, o.seconds) for k, v in self.style_time.items() if k in o.styles))
            if o.type == 'stage_sequence':
                current = self.current_stage(o)
                item.update(stages=[{'id': st.id, 'label': st.label, 'intensity': st.intensity, 'seconds': st.seconds,
                                     'elapsed': min(self.stage_time.get(st.id, 0), st.seconds), 'done': self.stage_time.get(st.id, 0) >= st.seconds,
                                     'current': bool(self.session_id) and current is st} for st in o.stages],
                            elapsed=sum(min(self.stage_time.get(st.id, 0), st.seconds) for st in o.stages),
                            total=sum(st.seconds for st in o.stages), tolerance=o.tolerance)
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
        # The mission completed in the running session, so its companion can still be told until that session ends.
        self.finished = None
        # Verified mission moments for the companion to react to; the observer hands them to the speech service.
        self.cues = []
        try:
            raw = store.read(PROGRESS_FILE, MISSING)
            # Only a missing file starts fresh; every existing file, even one holding null, must validate.
            self.progress = Progress(schema_version=SCHEMA_VERSION) if raw is MISSING else Progress.model_validate(migrate(raw))
        except (ValueError, OSError, ValidationError):
            self.progress = Progress(schema_version=SCHEMA_VERSION)
            self.error = 'Campaign progress could not be read. The file was left as it is and the campaign is unavailable; Freeplay is not affected.'
        self._settle_completion(self.progress)
        active = self.progress.active
        if active and not self._mission(active.campaign, active.mission):
            self.progress.active = None  # Its definition is gone (content removed); nothing else changes.
        if self.progress.active:
            self.attempt = Attempt(self._mission(self.progress.active.campaign, self.progress.active.mission))

    def _settle_completion(self, progress):
        """Chapter and campaign completion follow from the completed missions under the current definitions:
        a completion reward a completed mission now carries (Chapter 1's, after the version 2 migration) is
        granted with that mission's first completion time. Nothing is written until the next save."""
        for campaign in self.book.campaigns:
            record = progress.campaigns.get(campaign.id)
            if not record: continue
            for mission in campaign.missions:
                entry = record.missions.get(mission.id)
                if not entry: continue
                for reward in mission.rewards:
                    if reward.type in COMPLETION_REWARDS and reward.key not in record.rewards:
                        record.rewards[reward.key] = RewardRecord(earned_at=entry.first_completed_at, mission=mission.id)
            for key, earned in record.rewards.items():
                kind, _, rid = key.partition(':')
                if kind == 'chapter_complete' and rid not in record.chapters: record.chapters[rid] = ChapterRecord(completed_at=earned.earned_at)
                if kind == 'campaign_complete' and rid == campaign.id and not record.completed_at: record.completed_at = earned.earned_at

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
        limit = self.attempt.mission.settings_control
        if limit.after and self.attempt.done.get(limit.after): return frozenset(limit.then_allowed)
        return frozenset(limit.allowed)

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
                    'chapter': m.story.chapter if m.story else None,
                    'narrative_draft': bool(block and block.draft()),
                    'briefing': block.briefing.model_dump(exclude_none=True) if block else None})
            done = sum(1 for m in c.missions if m.id in record.missions and not m.optional)
            total = sum(1 for m in c.missions if not m.optional)
            chapters = []
            for ch in sorted(c.chapters, key=lambda ch: ch.number):
                members = [m for m in missions if m['chapter'] == ch.number and not m['optional']]
                chapters.append({'number': ch.number, 'id': ch.id, 'title': ch.title, 'summary': ch.summary,
                    'completed': ch.id in record.chapters, 'completed_at': record.chapters[ch.id].completed_at if ch.id in record.chapters else None,
                    'available': any(m['state'] != 'locked' for m in members),
                    'progress': {'completed': sum(1 for m in members if m['completions']), 'total': len(members)}})
            campaigns.append({'id': c.id, 'title': c.title, 'description': c.description, 'artwork': c.artwork, 'chapters': chapters,
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
        self.finished = None

    # -- what the companion is told
    def _cue(self, kind, mission, session_id, objective=None):
        campaign = self.book.campaign(self.progress.active.campaign if self.progress.active else self.finished['campaign'])
        return {'kind': kind, 'campaign': campaign.id, 'campaign_title': campaign.title, 'mission': mission.id,
                'mission_title': mission.title, 'order': mission.order, 'companion': mission.companion,
                'session_id': session_id, 'objective': objective.label if objective else None,
                'generation': self.attempt.generation if self.attempt else None,
                'campaign_complete': bool(kind == 'mission_complete' and self.finished and self.finished['campaign_complete']),
                'chapter': self.finished.get('chapter') if kind == 'mission_complete' and self.finished else None}

    def take_cues(self):
        cues, self.cues = self.cues, []
        return cues

    def model_context(self, model, report):
        """A short factual brief for the mission's own companion, or None. Every value in it is the campaign's
        verified state; it gives the companion the story frame and never a way to complete anything."""
        if self.error or not report: return None
        companion = self.identity(model)
        sid, status = report.get('session_id'), report.get('status')
        finished = self.finished
        if finished and finished['session_id'] == sid and sid is not None:
            mission = self._mission(finished['campaign'], finished['mission'])
            campaign = self.book.campaign(finished['campaign'])
            if not mission or mission.companion != companion: return None
            lines = [f'Campaign story: {campaign.title}, Mission {mission.order}, "{mission.title}". In this story you set the participant this mission.',
                     'Verified by EdgeLoop: the mission is complete and saved. The participant has already seen your completion message.']
            if finished.get('chapter'): lines.append(f'This mission completes the chapter "{finished["chapter"]}".')
            if finished['campaign_complete']: lines.append('This was the final mission: the campaign is complete.')
            lines.append('The session is still running; completing the mission does not end it, so carry on with the session as usual.'
                         if status in LIVE else 'The session has ended.')
            return {'companion': companion, 'mission': mission.id, 'state': 'completed', 'text': '\n'.join(lines),
                    'targets': sorted({o.count for o in mission.objectives if o.type == 'edge_count' and o.count})}
        attempt = self.attempt
        if not attempt or attempt.completed or attempt.mission.companion != companion: return None
        mission = attempt.mission
        campaign = self.book.campaign(self.progress.active.campaign)
        goals = [o for o in mission.objectives if o.type in GOAL_TYPES]
        lines = [f'Campaign story: {campaign.title}, Mission {mission.order}, "{mission.title}". In this story you set the participant this mission, and they have read your briefing for it.',
                 'The goal (EdgeLoop checks it, not you): ' + '; '.join(o.label for o in goals) + '.']
        if attempt.session_id == sid and sid is not None and status in LIVE:
            done = [o.label for o in goals if attempt.done.get(o.id)]
            progress = []
            for o in goals: progress += self._progress_words(attempt, o, report)
            lines.append('Verified progress in this session: ' + (', '.join(progress) if progress else 'not complete yet') + '.'
                         + (' Already reached: ' + '; '.join(done) + '.' if done else ''))
            lines.append('The mission is not complete yet. Do not say it is, and do not end or pause the session for it.')
        else:
            need = 'a session with you, with a heart-rate monitor and a toy connected'
            mode = mission.session.active_mode if mission.session else None
            if mode: need += f', in {MODE_WORDS.get(mode, mode)} mode'
            lines.append(f'The mission session has not started. To begin, the participant starts {need}. Nothing counts toward it yet.')
        block = (self.book.narratives.get(campaign.id).missions.get(mission.id) if self.book.narratives.get(campaign.id) else None)
        if block and block.director_context: lines.append(block.director_context)
        if mission.review: lines.append(self._review_words(campaign, mission))
        lines.append('If the participant asks what to do or how they are doing, answer from these lines. '
                     'Speak of the mission in your own words, as part of the story; do not quote its title like a label.')
        # How another mission is named, so talk of an earlier one is not read as a claim about this one.
        others = sorted({w for m in campaign.missions if m.id != mission.id for w in (m.title, f'Mission {m.order}')}
                        | {w for m in campaign.missions if m.companion != companion for w in (m.companion, *COMPANION_ALIASES.get(m.companion, ()))})
        return {'companion': companion, 'mission': mission.id, 'state': 'active', 'text': '\n'.join(lines),
                'targets': sorted({o.count for o in goals if o.type == 'edge_count' and o.count}), 'others': others}

    @staticmethod
    def _progress_words(attempt, o, report):
        clock = lambda n: f'{n // 60}:{n % 60:02d}'
        n = attempt.counts.get(o.id, 0)
        if o.type == 'edge_count': return [f'{min(n, o.count)} of {o.count} edges']
        if o.type == 'orgasm_count':
            words = f'{min(n, o.count)} of {o.count} reported orgasm' + ('s' if o.count > 1 else '')
            if o.after and not attempt.done.get(o.after): words += ' (only counted once the earlier goal is reached)'
            return [words]
        if o.type == 'style_stages':
            filled = attempt.done_styles(o)
            words = f'{len(filled)} of {o.count} play-style stages complete' + (' (' + ', '.join(STYLE_WORDS.get(k, k) for k in filled) + ')' if filled else '')
            style = report.get('experience')
            if report.get('goal') != 'tease': words += '; a game is on, so no stage time counts until it is switched off'
            elif style in filled: words += f'; the current play style, {STYLE_WORDS.get(style, style)}, has already filled a stage, so the participant should switch to a new one'
            elif style in o.styles: words += f'; current play style {STYLE_WORDS.get(style, style)}: {clock(min(attempt.style_time.get(style, 0), o.seconds))} of {clock(o.seconds)}'
            return [words]
        if o.type == 'stage_sequence':
            stage = attempt.current_stage(o)
            if not stage: return ['all assessment stages complete']
            number = o.stages.index(stage) + 1
            words = (f'stage {number} of {len(o.stages)}, "{stage.label}", at {stage.intensity}% intensity: '
                     f'{clock(attempt.stage_time.get(stage.id, 0))} of {clock(stage.seconds)}')
            now = report.get('intensity')
            if isinstance(now, int) and abs(now - stage.intensity) > o.tolerance:
                words += f'; intensity is now {now}%, so this stage\'s clock is paused until the participant sets {stage.intensity}%'
            return [words]
        return []

    def _review_words(self, campaign, mission):
        """What the saved progress verifies about the missions under review: completion, and kept results."""
        record = self.record(campaign.id)
        parts = []
        for mid in mission.review:
            m = campaign.mission(mid)
            if mid not in record.missions:
                parts.append(f'Mission {m.order} "{m.title}" ({m.companion}): no completion on record'); continue
            facts = []
            for o in m.objectives:
                value = record.records.get(f'{mid}.{o.id}')
                if value in (None, ''): continue
                facts.append(f'{value} edges' if o.type == 'edge_count' else f'{value} reported orgasms' if o.type == 'orgasm_count' else f'play styles {value}' if o.type == 'style_stages' else str(value))
            parts.append(f'Mission {m.order} "{m.title}" ({m.companion}): completed' + (' with ' + ', '.join(facts) if facts else ', with no further detail on record'))
        return 'Reports on file (saved by EdgeLoop, the only evidence you have): ' + '; '.join(parts) + '.'

    def abandon(self):
        progress = self.progress.model_copy(deep=True)
        progress.active = None
        self._save(progress)
        self.attempt = None
        self.cues = []

    # -- evidence
    def observe(self, report, events, model):
        """Called after the observer accepted an observation. Returns messages to publish (state changes, results)."""
        if self.error or not self.attempt or self.attempt.completed or not report: return []
        attempt, mission = self.attempt, self.attempt.mission
        if attempt.pending:
            # A completion that could not be saved is retried first; no later report can undo it.
            result = self._complete(attempt)
            if not result: return []
            self.cues.append(self._cue('mission_complete', mission, attempt.session_id))
            return [self.state(report, model), result]
        before = json.dumps(attempt.view(report, False), sort_keys=True)
        companion_ok = self.identity(model) == mission.companion
        sid, status, d = report.get('session_id'), report.get('status'), details(report)
        kinds = {e for e in events}
        out = []
        if attempt.session_id and sid != attempt.session_id:
            self._reset(attempt, 'session_changed')
        # Adopt the mission session: running, with the mission's companion, a real heart-rate monitor, a toy
        # and the required engine mode. Each condition is the engine's own reported state.
        moments = []
        if attempt.session_id is None and status == 'RUNNING' and companion_ok:
            if real_hr(report) and toy_ready(report) and self._mode_ok(mission, report):
                attempt.session_id = sid
                attempt.last_edges, attempt.last_orgasms = report.get('edges', 0), d.get('orgasm_count') or 0
                attempt.last_seconds, attempt.last_config = None, None
                attempt.reset_reason = None
                for o in mission.objectives:
                    if o.type in {'hr_monitor_connected', 'toy_connected', 'session_started'}: attempt.done[o.id] = True
                moments.append('start')
        if attempt.session_id == sid and attempt.session_id is not None:
            edges, orgasms = report.get('edges', 0), d.get('orgasm_count') or 0
            # Evidence counts only while every mission condition still holds: the mission companion, a real
            # heart-rate monitor (not the simulator), a toy and the mission's mode. Activity without them only
            # moves the baselines on, so it can never count later.
            eligible = companion_ok and real_hr(report) and toy_ready(report) and self._mode_ok(mission, report)
            # An orgasm is a rise of the engine's counter (I came; Finished me in Survival and Calibration, once
            # confirmed) or an accepted Came Early, which ends the session without raising it. Each is its own report.
            # The completion_reported flag is never evidence: Finished me sets it before its confirm, so a
            # cancelled Finished me leaves it set (then Edged ends Calibration with no orgasm).
            new_orgasms = max(0, orgasms - attempt.last_orgasms) + (1 if 'came_early' in kinds else 0)
            new_edges = max(0, edges - attempt.last_edges)
            met_before = {k for k, v in attempt.done.items() if v}
            if eligible:
                attempt.edges += new_edges
                attempt.orgasms += new_orgasms
                for o in mission.objectives:
                    # An `after` objective counts only events that come once its predecessor was already met.
                    if o.type not in COUNTED or (o.after and o.after not in met_before): continue
                    new = new_edges if o.type == 'edge_count' else new_orgasms
                    old = attempt.counts.get(o.id, 0)
                    attempt.counts[o.id] = old + new
                    moments += [f'{o.id}:{n}' for n in o.milestones if old < n <= old + new]
            # Counters only grow inside a session; an IDLE reset to 0 must not count backwards or double.
            attempt.last_edges, attempt.last_orgasms = max(attempt.last_edges, edges), max(attempt.last_orgasms, orgasms)
            moments += self._credit_time(attempt, report, eligible)
            calibrated = d.get('terminal_outcome') == 'calibration_completed' or 'completion_accepted' in kinds
            ended_ok = companion_ok and real_hr(report) and self._mode_ok(mission, report)
            for o in mission.objectives:
                if o.type in COUNTED and attempt.counts.get(o.id, 0) >= o.count: attempt.done[o.id] = True
                if o.type == 'style_stages' and len(attempt.done_styles(o)) >= o.count: attempt.done[o.id] = True
                if o.type == 'stage_sequence' and attempt.current_stage(o) is None: attempt.done[o.id] = True
                if o.type == 'calibration_completed' and calibrated and ended_ok: attempt.done[o.id] = True
                if o.type == 'calibration_saved' and calibrated and ended_ok and d.get('calibration_saved') is True:
                    metric = d.get('dual_max_bpm') if d.get('calibration_pass') == 'dual' else d.get('single_max_bpm')
                    if isinstance(metric, int):
                        attempt.done[o.id] = True
                        attempt.metric = {'calibration_pass': d.get('calibration_pass'), 'max_bpm': metric}
            if all(attempt.done.get(o.id) for o in mission.objectives):
                result = self._complete(attempt)
                if result:
                    out.append(result)
                    self.cues.append(self._cue('mission_complete', mission, sid))
            elif status == 'IDLE':
                # The session ended before the mission was done: the next session starts the counts again.
                self._reset(attempt, 'session_ended')
            else:
                moments += [f'{o.id}:done' for o in mission.objectives if o.type in GOAL_TYPES and attempt.done.get(o.id) and o.id not in met_before]
                out += self._moments(attempt, moments)
                if companion_ok and not any(o.type == 'calibration_completed' for o in mission.objectives):
                    # A goal reached while another still remains; setup items (strap, toy, session) are not story moments.
                    # In Calibration, Finished me reports the orgasm and ends the run a moment later: one moment, one card.
                    # A goal with its own scripted line is marked by that line, not also by the model.
                    scripted = self._narrative(mission)
                    for o in mission.objectives:
                        if o.type in GOAL_TYPES and attempt.done.get(o.id) and o.id not in attempt.cued:
                            attempt.cued.add(o.id)
                            if scripted and f'{o.id}:done' in scripted.milestones: continue
                            self.cues.append(self._cue('objective_reached', mission, sid, o))
        elif moments:
            out += self._moments(attempt, moments)
        if any(m['type'] == 'mission_result' for m in out):
            out.insert(0, self.state(report, model))
        elif json.dumps(attempt.view(report, False), sort_keys=True) != before:
            # Only the try changed (a count, a stage clock): a small update, not the whole campaign view,
            # since stage clocks change every second.
            out.insert(0, self.progress_update(report, model))
        return out

    def progress_update(self, report=None, model=None):
        attempt = self.attempt.view(report, bool(model) and self.identity(model) == self.attempt.mission.companion) if self.attempt else None
        return {'type': 'campaign_progress', 'active': self.progress.active.model_dump() if self.progress.active else None,
                'attempt': attempt, 'notice': self.notice}

    def _credit_time(self, attempt, report, eligible):
        """Credit active running time to the play style or stage in effect. An interval counts only when the
        observations at both ends were running, eligible and in the same configuration, so a pause, a setting
        change or a gap makes that interval count for nothing. Returns the progress moments reached."""
        seconds = report.get('seconds')
        config = (report.get('status'), report.get('experience'), report.get('goal'), report.get('intensity'), bool(eligible))
        last_seconds, last = attempt.last_seconds, attempt.last_config
        attempt.last_seconds, attempt.last_config = seconds, config
        if not isinstance(seconds, int) or not isinstance(last_seconds, int) or not last: return []
        step = seconds - last_seconds
        if not 0 < step <= MAX_STEP_SECONDS or not (config[4] and last[4]) or config[0] != 'RUNNING' or last[0] != 'RUNNING': return []
        moments = []
        for o in attempt.mission.objectives:
            if attempt.done.get(o.id): continue
            if o.type == 'style_stages':
                style = config[1]
                # One play style fills at most one stage; with a game on (anything but a plain tease) nothing counts.
                if style != last[1] or style not in o.styles or config[2] != 'tease' or last[2] != 'tease': continue
                filled = attempt.filled.setdefault(o.id, [])
                if style in filled: continue
                attempt.style_time[style] = attempt.style_time.get(style, 0) + step
                if attempt.style_time[style] >= o.seconds:
                    filled.append(style)
                    if len(filled) < o.count: moments.append(f'{o.id}:{len(filled)}')
            if o.type == 'stage_sequence':
                stage = attempt.current_stage(o)
                ok = lambda v: isinstance(v, int) and abs(v - stage.intensity) <= o.tolerance
                if not stage or not (ok(config[3]) and ok(last[3])): continue
                attempt.stage_time[stage.id] = min(stage.seconds, attempt.stage_time.get(stage.id, 0) + step)
                following = attempt.current_stage(o)
                if attempt.stage_time[stage.id] >= stage.seconds and following: moments.append(f'{o.id}:{following.id}')
        return moments

    def _narrative(self, mission):
        campaign_id = self.progress.active.campaign if self.progress.active else None
        narrative = self.book.narratives.get(campaign_id) if campaign_id else None
        return narrative.missions.get(mission.id) if narrative else None

    def _moments(self, attempt, keys):
        """Scripted lines for progress moments, each shown once per try. Only moments with a line are sent."""
        block = self._narrative(attempt.mission)
        out = []
        for key in keys:
            if key in attempt.marked or not block or key not in block.milestones: continue
            attempt.marked.add(key)
            out.append({'type': 'mission_milestone', 'campaign': self.progress.active.campaign, 'mission': attempt.mission.id,
                        'key': key, 'session_id': attempt.session_id, 'line': block.milestones[key].model_dump(exclude_none=True)})
        return out

    @staticmethod
    def _mode_ok(mission, report):
        return not mission.session or not mission.session.active_mode or report.get('active_mode') == mission.session.active_mode

    def cue_valid(self, cue):
        """Is a queued mission moment still true? A completion stays true for its session; a goal reached
        belongs to one try, so a reset, an abandon or a completed mission makes it stale."""
        if self.error: return False
        if cue['kind'] == 'mission_complete':
            return bool(self.finished and self.finished['mission'] == cue['mission'] and self.finished['session_id'] == cue['session_id'])
        attempt = self.attempt
        return bool(attempt and not attempt.completed and attempt.mission.id == cue['mission'] and attempt.session_id == cue['session_id']
                    and attempt.generation == cue.get('generation'))

    def _reset(self, attempt, reason):
        attempt.session_id = None; attempt.done = {}; attempt.edges = attempt.orgasms = 0
        attempt.last_edges = attempt.last_orgasms = None; attempt.metric = None; attempt.reset_reason = reason
        attempt.counts = {}; attempt.style_time = {}; attempt.stage_time = {}; attempt.filled = {}; attempt.marked = set()
        attempt.last_seconds = attempt.last_config = None
        attempt.cued = set(); attempt.generation += 1

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
        # Verified results the campaign keeps for later missions to refer to (the latest completion's).
        for o in mission.objectives:
            if o.type in COUNTED: record.records[f'{mission.id}.{o.id}'] = attempt.counts.get(o.id, 0)
            if o.type == 'style_stages': record.records[f'{mission.id}.{o.id}'] = ', '.join(STYLE_WORDS.get(k, k) for k in attempt.done_styles(o))
        chapter_done = next((r.id for r in mission.rewards if r.type == 'chapter_complete' and r.id not in record.chapters), None)
        if chapter_done: record.chapters[chapter_done] = ChapterRecord(completed_at=stamp)
        campaign_done = any(r.type == 'campaign_complete' for r in mission.rewards) and record.completed_at is None
        if campaign_done: record.completed_at = stamp
        progress.active = None
        open_before = {m.id for m in campaign.missions if self.mission_state(campaign, m) in {'available', 'completed', 'active'}}
        try:
            self._save(progress)
        except (ValueError, OSError):
            attempt.pending = True
            self.notice = 'Mission complete, but progress could not be saved. Check free disk space; it will be saved on the next update.'
            logger.warning('Campaign progress could not be saved')
            return None
        attempt.completed = True
        self.notice = None
        chapter = next((ch for ch in campaign.chapters if ch.id == chapter_done), None)
        self.finished = {'campaign': campaign.id, 'mission': mission.id, 'session_id': attempt.session_id,
                         'campaign_complete': bool(campaign_done), 'chapter': chapter.title if chapter else None}
        narrative = self.book.narratives.get(campaign.id)
        block = narrative.missions.get(mission.id) if narrative else None
        newly = [m.id for m in campaign.missions if m.id not in open_before and self.mission_state(campaign, m) == 'available']
        result = {'type': 'mission_result', 'campaign': campaign.id, 'mission': mission.id, 'title': mission.title,
                  'companion': mission.companion, 'replay': replay, 'earned': earned, 'unlocked_missions': newly,
                  'objectives': attempt.view(None, True)['objectives'], 'records': dict(record.records),
                  'completion': block.completion.model_dump(exclude_none=True) if block else None,
                  'chapter_complete': {'id': chapter.id, 'number': chapter.number, 'title': chapter.title} if chapter else None,
                  'chapter_completion': narrative.chapters[chapter.id].model_dump(exclude_none=True) if chapter and narrative and chapter.id in narrative.chapters else None,
                  'campaign_complete': bool(campaign_done),
                  'campaign_completion': narrative.campaign_complete.model_dump() if campaign_done and narrative and narrative.campaign_complete else None}
        self.attempt = None
        return result


CAMPAIGN_CARD = 'campaign_moment'


def card_brief(cue, status):
    """The task for a companion's reaction to a verified mission moment."""
    where = f'your mission "{cue["mission_title"]}" ({cue["campaign_title"]}, Mission {cue["order"]})'
    if cue['kind'] == 'objective_reached':
        return (f'React to a verified mission moment: in {where}, the participant has just reached this goal: '
                f'"{cue["objective"]}". The mission is not complete yet, because another goal remains. '
                'Mark the moment in your own voice, as the one running this mission.')
    text = (f'React to a verified mission moment: the participant has just completed {where}, and EdgeLoop saved it. '
            'Your completion message is already on screen, so do not repeat it and do not announce the next mission. '
            'Add one short, personal remark in your own voice.')
    if cue.get('chapter'): text += f' This mission completes the chapter "{cue["chapter"]}".'
    if cue.get('campaign_complete'): text += ' This was the final mission: the campaign is complete.'
    text += ' The session is still running and can carry on.' if status in LIVE else ' The session has ended.'
    return text
