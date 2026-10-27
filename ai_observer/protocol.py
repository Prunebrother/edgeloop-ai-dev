"""AGPL-3.0-only. Closed, bounded v1 observation/chat protocol; no commands."""
from typing import Annotated, Literal
from pydantic import Field, TypeAdapter, model_validator
from companion_ai.models import StrictModel, ModelSelection

Identifier = Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]
Mode = Literal['classic','finisher','milker','shortener','headplay','ultimate','ruin']
Goal = Literal['tease','survival','edgetrain','oracle','calibrate','nnn']

class Auth(StrictModel):
    version: Literal[1]
    type: Literal['auth']
    token: str = Field(min_length=32,max_length=128)
    browser_id: Identifier

class Devices(StrictModel):
    simulated_hr: bool
    hr_ready: bool
    toy_ready: bool
    ble: bool
    handy: bool
    intiface: bool
    tcode: bool
    vacuglide: bool

class Safety(StrictModel):
    signal: Literal['ok','holding','stale','missing']
    no_contact: bool
    watchdog_paused: bool
    fault: Literal['none','signal_lost','no_contact','device_unready']

class Movement(StrictModel):
    primary: int = Field(ge=0,le=100)
    secondary: int = Field(ge=0,le=100)
    stroke_min: int = Field(ge=0,le=100)
    stroke_max: int = Field(ge=0,le=100)
    @model_validator(mode='after')
    def ordered(self):
        if self.stroke_min>self.stroke_max: raise ValueError('Invalid stroke observation')
        return self

class ProjectionDetails(StrictModel):
    captured_at_ms: int = Field(ge=0,le=9007199254740991)
    hr_recorded_at_ms: int | None = Field(ge=0,le=9007199254740991)
    hr_live: bool | None = None
    resting_bpm: int | None = Field(ge=30,le=250)
    single_max_bpm: int | None = Field(ge=30,le=250)
    dual_max_bpm: int | None = Field(ge=30,le=250)
    pauses: int | None = Field(ge=0,le=1000000)
    calibration_pass: Literal['none','primary','dual']
    warmup_active: bool | None
    warmup_remaining_seconds: int | None = Field(ge=0,le=86400)
    ease_down_seconds: int | None = Field(ge=0,le=3600)
    rampdown_seconds: int | None = Field(ge=0,le=3600)

    @model_validator(mode='after')
    def timestamps(self):
        if self.hr_recorded_at_ms is not None and self.hr_recorded_at_ms>self.captured_at_ms:
            raise ValueError('A measurement cannot follow capture time')
        return self

class Snapshot(StrictModel):
    session_id: Identifier
    status: Literal['IDLE','RUNNING','PAUSED','RAMPDOWN']
    seconds: int = Field(ge=0,le=31536000)
    experience: Mode
    active_mode: Literal['classic','finisher','milker','shortener','headplay','ultimate','ruin','survival','oracle','edgetrain','calibrate']
    goal: Goal
    hr: int | None = Field(ge=35,le=250)
    effective_max: int = Field(ge=30,le=400)
    pullback: int | None = Field(ge=1,le=400)
    trend: Literal['unknown','steady','rising','falling']
    edges: int = Field(ge=0,le=1000000)
    intensity: int = Field(ge=50,le=150)
    movement: Movement
    devices: Devices
    safety: Safety
    details: ProjectionDetails | None = None

    @model_validator(mode='after')
    def consistent_projection(self):
        if self.details is None:return self  # Old v1 clients: additional facts remain unknown.
        if self.hr is not None and not self.devices.hr_ready:raise ValueError('Reading without a ready source')
        if self.devices.simulated_hr and not self.devices.hr_ready:raise ValueError('Simulator source not ready')
        if self.devices.hr_ready and not (self.devices.simulated_hr or self.devices.ble):raise ValueError('Unknown ready HR source')
        if self.details.warmup_active and self.status!='RUNNING':raise ValueError('Warm-up badge is only active while running')
        if self.devices.toy_ready and not any([self.devices.handy,self.devices.intiface,self.devices.tcode,self.devices.vacuglide]):raise ValueError('Toy readiness without a connection')
        return self

EventKind = Literal['session_started','pause','stop','session_resumed','mode_changed','edge',
                    'signal_lost','signal_restored','no_contact','device_changed','milestone','experience_changed','goal_changed','intensity_changed','threshold_changed']
class Event(StrictModel):
    id: Identifier
    kind: EventKind
    at_ms: int | None = Field(default=None,ge=0,le=9007199254740991)
    session_id: Identifier | None = None

class Observation(StrictModel):
    version: Literal[1]
    type: Literal['observation']
    epoch: Identifier
    sequence: int = Field(ge=0,le=9007199254740991)
    snapshot: Snapshot
    events: list[Event] = Field(max_length=16)

class Select(StrictModel):
    version: Literal[1]
    type: Literal['select_model']
    selection: ModelSelection
    thinking: bool | None = None

class Chat(StrictModel):
    version: Literal[1]
    type: Literal['chat']
    text: str = Field(min_length=1,max_length=2000)
    model: str = Field(min_length=1,max_length=120)

class Models(StrictModel):
    version: Literal[1]
    type: Literal['list_models']

class Cancel(StrictModel):
    version: Literal[1]
    type: Literal['cancel_generation']

Messages = TypeAdapter(Annotated[Observation|Select|Chat|Models|Cancel,Field(discriminator='type')])


def _schema_paths(node):
    known=set()
    if isinstance(node,dict):
        known.update(node.get('properties',{}))
        if isinstance(node.get('const'),str):known.add(node['const'])
        for child in node.values():known.update(_schema_paths(child))
    elif isinstance(node,list):
        for child in node:known.update(_schema_paths(child))
    return known

_SCHEMA_PATHS=_schema_paths(Messages.json_schema())

def safe_validation_errors(error):
    # Extra field names can themselves contain secrets. Retain only schema names.
    return [{'path':[part if isinstance(part,int) or part in _SCHEMA_PATHS else '<extra-field>' for part in item['loc']],
             'code':item['type']} for item in error.errors(include_input=False,include_url=False,include_context=False)[:8]]
