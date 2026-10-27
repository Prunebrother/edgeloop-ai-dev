"""AGPL-3.0-only. Closed, bounded v1 observation/chat protocol; no commands."""
from typing import Annotated, Literal
from pydantic import Field, TypeAdapter, model_validator
from edgeloop_ai.models import StrictModel, ModelSelection

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

class Snapshot(StrictModel):
    session_id: Identifier
    status: Literal['IDLE','RUNNING','PAUSED','RAMPDOWN']
    seconds: int = Field(ge=0,le=31536000)
    experience: Mode
    active_mode: Literal['classic','finisher','milker','shortener','headplay','ultimate','ruin','survival','oracle','edgetrain','calibrate']
    goal: Goal
    hr: int | None = Field(ge=35,le=250)
    effective_max: int = Field(ge=30,le=400)
    pullback: int = Field(ge=1,le=400)
    trend: Literal['unknown','steady','rising','falling']
    edges: int = Field(ge=0,le=1000000)
    intensity: int = Field(ge=50,le=150)
    movement: Movement
    devices: Devices
    safety: Safety

EventKind = Literal['session_started','pause','stop','session_resumed','mode_changed','edge',
                    'signal_lost','signal_restored','no_contact','device_changed','milestone']
class Event(StrictModel):
    id: Identifier
    kind: EventKind

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
