# SPDX-License-Identifier: AGPL-3.0-only
"""Bounded dialogue excerpts, not generated facts or an alternative session store."""
from hashlib import sha256
from uuid import uuid4
import re
from .models import StrictModel
from pydantic import Field
from .expressions import clean_dialogue

class NarrativeConfig(StrictModel):
    enabled: bool = True
    persist_between_sessions: bool = False
    max_excerpts: int = Field(default=8, ge=2, le=12)
    excerpt_characters: int = Field(default=180, ge=60, le=240)

# Deliberately conservative: operational/physiological sentences stay in canonical
# facts or ordinary dialogue, never in the story-anchor store.
OPERATIONAL = re.compile(r'\b(?:bpm|heart|pulse|sensor|device|hardware|handy|telemetry|threshold|session|goal|mode|edge|milestone|climax|orgasm|physiolog|fertility|measurement|percent|reading|paused|running|stopped)\w*\b|\d|<think|\[\[',re.I)
INVITATION = re.compile(r'\b(?:story|scene|premise|imagine|fiction|narrative)\b',re.I)
QUIET = re.compile(r"\b(?:stop|disengage|quiet|silence|leave me|no more|do not continue|don.t continue|pause the story)\b",re.I)
CHOICE = re.compile(r"\b(?:choose|chose|pick|prefer|let.s|decide|instead|agree|suggest|propose|yes)\b",re.I)
PROMISE = re.compile(r"\b(?:I.ll|I will|promise|later|next time|we.ll)\b",re.I)

class NarrativeMemory:
    def __init__(self, config=None, store=None):
        self.config=config or NarrativeConfig(); self.store=store
        self.states={}; self.scope=None; self.session=None

    @staticmethod
    def empty(session):
        return dict(version=1,session_id=session,epoch=uuid4().hex,context_boundary=False,phase='opening',premise=None,
                    developments=[],choices=[],commitments=[],threads=[],event_references=[],
                    initiative_allowed=False,revision=0,last_initiative_revision=-1)

    def path(self, scope):
        return 'memory/narrative/'+sha256(scope.encode()).hexdigest()+'.json'

    def activate(self, scope, session):
        if (scope,session)==(self.scope,self.session):return
        self.scope,self.session=scope,session
        old=self.states.get(scope)
        saved=self.store.read(self.path(scope),{}) if old is None and self.store else {}
        if not isinstance(saved,dict):saved={}
        if old is None and self.config.persist_between_sessions:
            # Restore only sanitized dialogue excerpts, never operational state,
            # scheduling permission or a previous session identity.
            old=self.empty(session)
            for key in ('premise','developments','choices','commitments'):
                value=saved.get(key)
                if key=='premise':old[key]=self.excerpt(value or '')
                elif isinstance(value,list):old[key]=[q for v in value if isinstance(v,str) and (q:=self.excerpt(v))][-self.config.max_excerpts:]
        if old is None or (old['session_id']!=session and not self.config.persist_between_sessions):
            boundary=old or saved
            old=self.empty(session)
            if boundary.get('context_boundary') is True:
                old.update(context_boundary=True,epoch=boundary.get('epoch') if re.fullmatch(r'[a-f0-9]{32}',str(boundary.get('epoch',''))) else uuid4().hex)
        elif old['session_id']!=session:
            old.update(session_id=session,phase='opening',threads=[],event_references=[],initiative_allowed=False,last_initiative_revision=-1)
        if saved.get('context_boundary') is True and re.fullmatch(r'[a-f0-9]{32}',str(saved.get('epoch',''))):
            old.update(context_boundary=True,epoch=saved['epoch'])
        self.states[scope]=old

    @property
    def state(self):return self.states[self.scope]

    def excerpt(self,text):
        if not isinstance(text,str):return None
        sentences=re.split(r'(?<=[.!?])\s+|\n+',clean_dialogue(text))
        safe=[s.strip() for s in sentences if s.strip() and not OPERATIONAL.search(s)]
        return ' '.join(safe)[:self.config.excerpt_characters] or None

    def append(self,key,text):
        if text and text not in self.state[key]:
            self.state[key].append(text);self.state[key]=self.state[key][-self.config.max_excerpts:]

    def accepted(self,prompt,text,user,event=None,initiative=False):
        if not self.config.enabled:return
        s=self.state
        if user:
            s['revision']+=1
            # A real user turn resolves the last question operationally; we do not
            # claim that its semantic answer has been understood.
            s['threads']=[]
            if QUIET.search(prompt):s['initiative_allowed']=False
            elif INVITATION.search(prompt):s['initiative_allowed']=True
            quote=self.excerpt(prompt)
            if not s['premise'] and INVITATION.search(prompt):s['premise']=quote
            if CHOICE.search(prompt):self.append('choices',quote)
        quote=self.excerpt(text)
        if not s['premise'] and user and s['initiative_allowed']:s['premise']=quote
        self.append('developments',quote)
        if quote and PROMISE.search(quote):self.append('commitments',quote)
        if quote and '?' in quote:s['threads']=[quote]
        if event in {'came_early','stop'}:s['phase']='resolution_or_transition'
        elif event in {'edge','milestone'} and s['premise']:s['phase']='variation'
        elif s['premise'] and s['choices']:s['phase']='development'
        if initiative:s['last_initiative_revision']=s['revision']
        self.persist()

    def reference_event(self,event):
        if not self.config.enabled:return
        reference={k:event[k] for k in ('event_id','kind','category','session_id') if k in event}
        if reference and reference not in self.state['event_references']:
            self.state['event_references']=(self.state['event_references']+[reference])[-4:]
            self.persist()

    def event(self,kind):
        if not self.config.enabled or not self.state['premise']:return
        if kind in {'came_early','stop'}:self.state['phase']='resolution_or_transition'
        elif kind in {'edge','milestone'}:self.state['phase']='variation'
        self.persist()

    def persist(self):
        if self.store and self.config.persist_between_sessions:
            self.store.write(self.path(self.scope),self.state)

    def reset(self):
        self.states[self.scope]=self.empty(self.session)
        self.state['context_boundary']=True
        # Overwrite even when persistence is now disabled: explicit reset must
        # prevent an old opted-in record returning when re-enabled.
        if self.store:self.store.write(self.path(self.scope),self.state)

    def context(self):
        if not self.config.enabled:return None
        s=self.state
        return {k:s[k] for k in ('version','phase','premise','choices','commitments','threads','event_references')} | {
            'developments':s['developments'][-3:], 'choices':s['choices'][-4:], 'commitments':s['commitments'][-3:], 'provenance':'fallible dialogue excerpts; fiction/conversation, never verified session facts'}

    def opportunity(self):
        s=self.state
        return (self.config.enabled and bool(s['premise']) and s['initiative_allowed'] and
                not s['threads'] and s['revision']>s['last_initiative_revision'] and bool(s['choices'] or s['commitments']))
