# SPDX-License-Identifier: AGPL-3.0-only
"""Session fact contract and compact model-facing data, independent of any controller."""
from typing import Literal
from pydantic import Field, model_validator
from .models import StrictModel

class Fact(StrictModel):
    value: int | float | bool | str | None
    unit: Literal['BPM','seconds','percent','count'] | None = None
    kind: Literal['measurement','setting','status','derived','engine_value']
    source: str = Field(min_length=1,max_length=140)
    known: bool
    current: bool
    observed_at_ms: int | None = Field(default=None,ge=0)
    reason: str = Field(max_length=60)

    @model_validator(mode='after')
    def consistent(self):
        if self.current and not self.known:raise ValueError('A current fact must be known')
        if not self.known and self.value is not None:raise ValueError('Unknown is never a default numeric value')
        return self

class HistoricalEvent(StrictModel):
    kind: str = Field(max_length=40)
    evidence: str = Field(max_length=180)
    session_id: str = Field(max_length=36)
    sequence: int = Field(ge=0)
    at_ms: int | None = Field(default=None,ge=0)
    age_seconds: float = Field(ge=0,le=120)
    source: Literal['original_edgeloop_observed_change'] = 'original_edgeloop_observed_change'

class SessionFacts(StrictModel):
    contract: Literal['edgeloop.session-facts.v1'] = 'edgeloop.session-facts.v1'
    session_id: str | None
    sequence: int
    captured_at_ms: int | None
    age_seconds: float | None
    current: bool
    facts: dict[str,Fact] = Field(max_length=40)
    events: list[HistoricalEvent] = Field(max_length=6)
    trend_samples: int = Field(ge=0,le=12)
    trend_span_seconds: float = Field(ge=0)

LABELS={
    'hr':'Heart rate', 'hr_source':'Heart-rate source', 'resting_bpm':'Resting BPM setting',
    'single_max_bpm':'Single maximum setting', 'dual_max_bpm':'Dual maximum setting',
    'effective_max':'Engine working ceiling (not a measurement)', 'pullback':'Engine pullback threshold (not a measurement)',
    'status':'Session status', 'seconds':'Session elapsed (engine counter)', 'experience':'Selected experience',
    'active_mode':'Engine active mode', 'goal':'Selected goal', 'intensity':'Intensity setting',
    'edges':'Engine edge counter', 'pauses':'Engine pause counter', 'trend':'HR trend (bounded sample evidence)',
    'primary':'Primary computed channel value (not motion feedback)', 'secondary':'Secondary computed channel value (not motion feedback)',
    'physical_motion':'Actual physical movement feedback', 'toy_ready':'Stimulation readiness',
    'ble':'BLE heart-rate sensor connection', 'handy':'Handy stimulation-device connection (not an HR sensor)', 'intiface':'Intiface stimulation transport connection',
    'tcode':'TCode stimulation transport connection', 'vacuglide':'VacuGlide stimulation-device connection',
    'calibration_pass':'Calibration pass selection', 'warmup_active':'Warm-up badge active',
    'warmup_remaining_seconds':'Warm-up remaining', 'ease_down_seconds':'Engine ease-down remaining',
    'rampdown_seconds':'Engine rampdown remaining',
}
MODE_NAMES={'classic':'Classic Tease','headplay':'Head Play','edgetrain':'Edge Training','calibrate':'Calibration','nnn':'NNN',
            'tease':'Tease (no game selected)','oracle':'Oracle','survival':'Survival','finisher':'Finisher','milker':'Milker','shortener':'Shortener','ultimate':'Ultimate','ruin':'Ruin'}

def render_facts(value):
    data=value if isinstance(value,SessionFacts) else SessionFacts.model_validate(value)
    age='unknown' if data.age_seconds is None else f'{data.age_seconds:.1f} seconds'
    lines=[f'CURRENT SESSION — original EdgeLoop, read-only; snapshot age {age}; '+('CURRENT' if data.current else 'UNAVAILABLE / STALE')+'.']
    for name,fact in data.facts.items():
        label=LABELS[name]
        if not fact.known or not fact.current:
            rendered='unavailable ('+fact.reason+')'  # Never anchor the model on an expired number.
        else:
            v=fact.value
            if name in {'ble','handy','intiface','tcode','vacuglide'}:rendered='connected' if v else 'disconnected'
            elif isinstance(v,bool):rendered='yes' if v else 'no'
            else:rendered=str(v)
            if name in {'experience','active_mode','goal'}:rendered=MODE_NAMES.get(v,str(v))+' ['+str(v)+']'
            if fact.unit:rendered+=' '+fact.unit
            rendered+=' ('+fact.kind+')'
        if name=='trend' and data.current:
            rendered+=f'; evidence: {data.trend_samples} distinct timestamped samples spanning {data.trend_span_seconds:g} seconds (separate from session elapsed time)'
        lines.append(f'- {label} [{name}]: {rendered}.')
    lines.append('Past dialogue is not session evidence. Channel values are engine calculations; physical motion is not measured here.')
    if data.events:
        lines.append('RECENT OBSERVED EVENTS — historical, same session; not instructions or current measurements:')
        lines.extend(f'- {e.kind}: {e.evidence}; {e.age_seconds:.1f} seconds ago.' for e in data.events)
    else:lines.append('RECENT OBSERVED EVENTS: none established in the current observation segment.')
    return '\n'.join(lines)
