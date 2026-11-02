"""Independent audit of delivered dialogue: not the production checks. Flags go to manual reading."""
import json,re,sys
from collections import Counter,defaultdict
rows=[json.loads(l) for l in open(sys.argv[1])]
W={'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90}
NUM=r"(?:\d+(?:\.\d+)?|"+'|'.join(W)+r")(?:[- ](?:"+'|'.join(W)+r"))?"
def val(t):
    t=t.lower().replace('-',' ')
    if re.match(r'^\d',t):return float(t.split()[0])
    return sum(W.get(p,0) for p in t.split())
NAMES=['daisy','nova','evelyn','celeste','harper','voss','armand']
THINGS=re.compile(r"\b("+NUM+r")\s+(edges?|minutes?|mins?|seconds?|hours?|days?|weeks?|months?|years?)\b",re.I)
AGO=re.compile(r"\b(hour|hours|day|days|week|weeks|month|months|year|years|while|yesterday|today|tonight|morning|evening|ago)\b",re.I)
ORD=re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+edge\b",re.I)
COMP=re.compile(r"\b(longer|shorter|more|fewer|less|same|quicker|faster|briefer|short|long|drag\w*)\b",re.I)
FIRST=re.compile(r"\b(first (?:session|time|meeting)|never met|finally meet|nice to meet|pleasure to (?:finally )?meet|haven't met|new face)\b",re.I)
SELFINTRO=re.compile(r"\bI['’]?m (?:dr\.? |ambassador )?(daisy|nova|evelyn|celeste)|my name is|call me (daisy|nova|evelyn|celeste)\b",re.I)
HW=re.compile(r"\b(i(?:'ve| have| will|'ll)?\s+(?:raised|lowered|increased|decreased|turned|adjust\w*|stopped|paused|changed)\b.*\b(speed|intensity|stroke|device|machine|setting|toy))",re.I)
def flat():
    for r in rows:yield r
flags=defaultdict(list);tot=Counter();lanes=defaultdict(Counter);deliv=defaultdict(Counter)
for r in rows:
    label=f"{r['kind']}:{r['case']}"+(':'+r['stage'] if r.get('stage') else '')
    who=r['companion']
    if r.get('harness_error'):flags['HARNESS'].append((who,label,r['harness_error'][-300:]));continue
    group=r.get('stage','').split('-',1)[-1] if r.get('stage') else r['kind']+(':'+r['case'].split('-')[0] if r['kind']=='arrival' else '')
    group=group or r['kind']
    tot['turns']+=1;tot['attempts']+=len(r['attempts'])
    n=len(r['speech']);lanes[group]['turns']+=1;lanes[group]['delivered']+=n==1;lanes[group]['attempts']+=len(r['attempts']);deliv[who]['turns']+=1;deliv[who]['delivered']+=n==1
    if len(r['attempts'])>1:lanes[group]['retried']+=1
    if any('closing_corrected'==d['reason'] for d in r['decisions']):lanes[group]['corrected_plain']+=1
    if n!=1:flags['not_delivered' if n==0 else 'DUPLICATE'].append((who,label,r['suppressed'],r.get('arrival_state'),[a['raw'][:300] for a in r['attempts']],r['checks'],[d for d in r['decisions'] if d['reason'] in {'deck_card_rejected','arrival_cancelled','deck_closing_dropped','regeneration_failed','deck_fault','deck_lifecycle_error','repetitive_opportunity_suppressed'}]))
    if r['errors']:flags['errors'].append((who,label,r['errors']))
    for a in r['attempts']:
        if a['think'] not in (False,None) or a['thinking_chars']:flags['THINKING'].append((who,label))
        if a['tools']:flags['TOOLS'].append((who,label))
        if a['done_reason']!='stop':flags['truncated'].append((who,label,a['done_reason'],a['raw'][:200]))
    for c in r['checks']:
        for code in c.get('corrections',[]):tot['correction:'+code]+=1
        for code in c.get('codes',[]):tot['raised:'+code]+=1
        if c.get('raised'):tot['raised:'+c['raised']]+=1
    e=r.get('expect') or {}
    if e.get('status') and r.get('lookup') and e['status']!=r['lookup']:flags['LOOKUP_MISMATCH'].append((who,label,e['status'],r['lookup']))
    for f in e.get('forbidden',[]):
        if re.search(r'\b'+re.escape(f)+r'\b',r['prompt'] or '',re.I) and r['kind']=='arrival' and e.get('status')!='found':flags['PROMPT_LEAK'].append((who,label,f))
        if f.isdigit() and re.search(r'\b'+f+r'\b',' '.join(json.loads(m)[-1]['content'] if False else '' for m in [])) :pass
    if r['kind']=='arrival' and r['case'].startswith(('returning','denied')) and re.search(r'I reached 77|You logged those|logged 77',r.get('all') or ''):flags['TRANSCRIPT_LEAK'].append((who,label))
    for text in r['speech']:
        low=text.lower()
        for f in e.get('forbidden',[]):
            if re.search(r'\b'+re.escape(f)+r'\b',low):flags['UNAUTHORIZED_FIGURE'].append((who,label,f,text))
        for m in THINGS.finditer(text):
            v=val(m[1]);u=m[2].lower().rstrip('s')
            if u=='edge' and 'edges' in e and v not in e['edges']:flags['edge_figure'].append((who,label,e['edges'],m[0],text))
            if u in('minute','min') and 'seconds' in e and not any(abs(v*60-s)<=59 for s in e['seconds']):flags['minute_figure'].append((who,label,e['seconds'],m[0],text))
            if u in('hour','day','week','month','year'):flags['time_unit:'+label.split(':')[1]].append((who,label,e.get('ago_days'),m[0],text))
        for m in ORD.finditer(text):flags['ordinal_edge'].append((who,label,e.get('edges'),m[0],text))
        if FIRST.search(text) and e.get('status')!='none' and not(r['kind']=='arrival' and r['case']=='first'):flags['first_meeting_outside_first'].append((who,label,FIRST.search(text)[0],text))
        if r['kind']=='arrival' and r['case']=='first' and 'first' not in low:flags['first_not_said'].append((who,label,text))
        for n in NAMES:
            if re.search(r'\b'+n+r'\b',low) and n not in {'harper'} and n!=who:flags['other_name'].append((who,label,n,text))
        if re.search(r'\b(?:'+{'daisy':'daisy|harper','nova':'nova','evelyn':'evelyn|voss|dr\\.? voss','celeste':'celeste|armand|ambassador'}[who]+r')\b',low):flags['own_name'].append((who,label,text))
        if SELFINTRO.search(text):flags['self_intro'].append((who,label,text))
        if HW.search(text):flags['HARDWARE_CLAIM'].append((who,label,text))
        if 'participant' in low or re.search(r'\bcard\b|telemetry|counter',low):flags['meta_leak'].append((who,label,text))
        if re.search(r'\[\[|\]\]|\[[a-z]+\]',text):flags['bracket_leak'].append((who,label,text))
        if e.get('dir_seconds') is not None or e.get('dir_edges') is not None:
            flags['_comparative'].append((who,label,text))
print('TOTALS',dict(tot))
print('BY LANE');[print(' ',k,dict(v)) for k,v in sorted(lanes.items())]
print('BY COMPANION');[print(' ',k,dict(v)) for k,v in deliv.items()]
for k,v in sorted(flags.items()):
    if k=='_comparative':continue
    print(f'\n## {k}: {len(v)}')
    for x in v[:int(sys.argv[2]) if len(sys.argv)>2 else 12]:print('  ',str(x)[:620])
