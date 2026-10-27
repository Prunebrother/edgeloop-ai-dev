"""AGPL-3.0-only. Browser-reported data only; no motor or session clock."""
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
import time
from companion_ai.director import ConversationDirector

@dataclass(frozen=True)
class ObservedDevice:
    moving: bool | None = None
    velocity: int | None = None
    pattern: str = 'unknown'

class BrowserObservation:
    def __init__(self, clock=time.monotonic):
        self.clock=clock
        self.report=None
        self.received=None
        self.connected=False
        self.sequence=-1
        self.session_id=None
        self.samples=deque(maxlen=12)
        self.retired_sessions=deque(maxlen=64)

    def accept(self, message):
        if message.sequence<=self.sequence: return False
        if message.snapshot.session_id in self.retired_sessions:return False
        self.sequence=message.sequence
        if self.session_id!=message.snapshot.session_id:
            if self.session_id is not None:self.retired_sessions.append(self.session_id)
            self.samples.clear()
        self.report=message.snapshot.model_dump()
        self.session_id=message.snapshot.session_id
        self.received=self.clock();self.connected=True
        if self.hr is not None: self.samples.append((self.received,self.hr))
        return True

    def fresh(self): return self.connected and self.received is not None and self.clock()-self.received<=5
    @property
    def status(self): return self.report['status'] if self.report else 'UNKNOWN'
    @property
    def hr(self): return self.report['hr'] if self.report else None
    @property
    def trend(self): return self.report['trend'] if self.report else 'unknown'
    @property
    def emergency(self): return False  # No invented emergency latch: upstream owns its safety.
    @property
    def device(self):
        if not self.report: return ObservedDevice()
        m=self.report['movement']
        return ObservedDevice(m['primary']>0 or m['secondary']>0,m['primary'],self.report['experience'])
    def snapshot(self):
        return {'source':'original_edgeloop','read_only':True,'observation_fresh':self.fresh(),
                'status':self.status,'seconds':self.report['seconds'] if self.report else None,
                'hr':self.hr,'trend':self.trend,'device':self.device.__dict__,
                'reported_state':deepcopy(self.report)}
    def summary(self):
        return {'source':'original_edgeloop','read_only':True,'observation_fresh':self.fresh(),
                'observation_age_seconds':None if self.received is None else round(self.clock()-self.received,1),
                'state':deepcopy(self.report) if self.fresh() else None,
                'availability':'current observation' if self.fresh() else 'unavailable; do not assume the last readings or movement are current'}


# The shared Director filters a legacy flat session schema. Preserve its
# pacing/repetition/memory logic and attach only the validated browser projection.
class ObserverDirector(ConversationDirector):
    def context(self, snapshot, prompt, events, user, memory_enabled=True):
        result=super().context(snapshot,prompt,events,user,memory_enabled)
        return result | {key:snapshot[key] for key in (
            'source','read_only','observation_fresh','observation_age_seconds','state','availability') if key in snapshot}
