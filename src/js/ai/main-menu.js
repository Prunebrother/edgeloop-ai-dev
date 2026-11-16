// SPDX-License-Identifier: AGPL-3.0-only
// Main menu, Campaign and Mission screens, and the in-session mission banner.
// Presentation only: the observer owns campaign rules, evidence and saved progress
// (companion_ai/campaign.py). Text from the observer is always assigned with textContent.
import {CHARACTERS} from './artwork-manifest.js';

const LIVE=new Set(['RUNNING','PAUSED','RAMPDOWN']);
const STATE_LABEL={completed:'Completed',active:'In progress',available:'Available',locked:'Locked'};

function node(tag,attrs={},...children){
    const el=document.createElement(tag);
    for(const [k,v] of Object.entries(attrs)){
        if(v===null||v===undefined||v===false)continue;
        if(k==='class')el.className=v;else if(k==='text')el.textContent=v;else if(k.startsWith('on'))el.addEventListener(k.slice(2),v);
        else if(k==='dataset')Object.assign(el.dataset,v);else el.setAttribute(k,v===true?'':String(v));
    }
    el.append(...children.filter(c=>c!==null&&c!==undefined&&c!==false));
    return el;
}
const name=id=>CHARACTERS[id]?.name||id;
const clock=n=>`${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`;
const percent=(done,total)=>total?Math.round(100*done/total):0;
const SETTING_WORDS={intensity:'intensity',orgasm:'Force Orgasm',play_style:'play style',game:'game',endgame:'endgame',pause:'pause',stop:'stop'};
const portrait=(id,expression='neutral')=>CHARACTERS[id]?.expressions?.[expression]||CHARACTERS[id]?.expressions?.neutral||null;

export function mountMainMenu({send,status,selectCompanion,postLines,bannerHost}){
    let data=null,paired=false,view='home',campaignId=null,missionId=null,pendingStart=null,pendingLeave=false,result=null,commandError=null,lastFocus=null;
    const live=()=>LIVE.has(status());
    const root=node('div',{id:'main-menu',class:'game-menu',role:'dialog','aria-modal':'true','aria-labelledby':'main-menu-title'});
    const panel=node('div',{class:'game-menu-panel'});root.append(panel);
    document.body.prepend(root);
    // The engine's shortcuts (Space starts a session) must not fire behind the menu.
    root.addEventListener('keydown',e=>{
        if(e.key==='Escape'&&view!=='home'){e.preventDefault();back();}
        else if(e.key==='Tab'){const items=[...root.querySelectorAll('button:not([disabled]),[href],[tabindex="0"]')];
            if(items.length){const first=items[0],last=items.at(-1);
                if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
                else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}}
        else if(['ArrowDown','ArrowUp','ArrowRight','ArrowLeft'].includes(e.key)&&e.target.closest?.('[data-menu-list]')){
            const items=[...e.target.closest('[data-menu-list]').querySelectorAll(':scope > li > button:not([disabled]), :scope > button:not([aria-disabled])')];
            const i=items.indexOf(document.activeElement);
            if(i>=0){e.preventDefault();items[(i+(['ArrowDown','ArrowRight'].includes(e.key)?1:-1)+items.length)%items.length].focus();}
        }
        e.stopPropagation();
    });
    // The age gate and the setup wizard sit above the menu and keep their own keys and focus.
    const above=()=>['ageOverlay','wizardOverlay'].some(id=>{const e=document.getElementById(id);return e&&!e.classList.contains('hidden')&&getComputedStyle(e).display!=='none';});
    const focusMenu=()=>(panel.querySelector('[data-menu-list] button:not([disabled]):not([aria-disabled]), .game-menu-actions button:not([disabled]), .game-menu-back')||panel.querySelector('button'))?.focus({preventScroll:true});
    // Focus can sit outside the menu (after the wizard closes, or a click on the page behind): a key from there
    // must not reach the engine's document-level shortcuts. Capture on window runs before every other listener.
    const guard=e=>{
        if(root.hidden||above()||root.contains(e.target))return;
        e.stopImmediatePropagation();e.preventDefault();
        if(e.type==='keydown')focusMenu();
    };
    for(const type of ['keydown','keyup','keypress'])window.addEventListener(type,guard,true);
    const refocus=e=>{if(!root.hidden&&!above()&&!root.contains(e.target))queueMicrotask(focusMenu);};
    document.addEventListener('focusin',refocus);

    const campaign=()=>data?.campaigns?.find(c=>c.id===campaignId)||null;
    const mission=()=>campaign()?.missions.find(m=>m.id===missionId)||null;
    const open=(next=view)=>{view=next;root.hidden=false;document.body.classList.add('game-menu-open');render();};
    const close=()=>{root.hidden=true;document.body.classList.remove('game-menu-open');menuButton.disabled=false;(lastFocus||document.getElementById('companion-message'))?.focus?.();};
    const go=next=>{commandError=null;view=next;render();};
    const back=()=>go(view==='missions'?'campaigns':view==='briefing'||view==='results'?(campaignId?'missions':'home'):'home');

    function header(title,subtitle,backLabel){
        return node('header',{class:'game-menu-header'},
            backLabel?node('button',{type:'button',class:'game-menu-back',onclick:back},'← '+backLabel):null,
            node('p',{class:'eyebrow',text:'EdgeLoop AI'}),
            node('h1',{id:'main-menu-title',text:title}),
            subtitle?node('p',{class:'game-menu-sub',text:subtitle}):null);
    }
    function statusLine(){
        const text=commandError||(pendingLeave?'Leaving the mission…':null)||data?.error||data?.notice||(!paired?'Connecting to the companion service… Campaign needs it; Freeplay works without it.':null);
        return text?node('p',{class:'game-menu-status',role:'status',text}):null;
    }
    function renderHome(){
        const tile=(label,detail,onclick,disabled)=>node('button',{type:'button',class:'game-menu-tile',onclick:disabled?null:onclick,
            'aria-disabled':disabled?'true':null,dataset:{menuTile:label.toLowerCase().replace(/\s+/g,'-')}},node('strong',{text:label}),node('span',{text:detail}));
        const list=node('div',{class:'game-menu-tiles','data-menu-list':true},
            tile('Campaign','Story missions with the companions of Project EdgeLoop.',()=>go('campaigns')),
            tile('Freeplay','Every companion, every setting. EdgeLoop AI as you know it.',freeplay),
            tile('Companion Builder','Coming soon',null,true));
        // Only an error or a pending leave shows here; the connecting notice belongs to the Campaign screens.
        return [header('Main menu','Choose how you want to play.'),commandError||pendingLeave?statusLine():null,list];
    }
    // Freeplay carries no campaign rules: a mission in progress is left first (completed missions and rewards stay).
    function freeplay(){
        const active=data?.active,m=active&&data.campaigns.find(c=>c.id===active.campaign)?.missions.find(x=>x.id===active.mission);
        if(m){if(!confirm(`Freeplay leaves the mission in progress (${m.title}). Completed missions and rewards are kept. Continue?`))return;
            // The menu stays until the observer confirms the mission was left: until then its rules still apply.
            if(!send({version:1,type:'campaign',action:'abandon'})){commandError='The companion service could not be reached, so the mission is still in progress.';render();return;}
            pendingLeave=true;commandError=null;render();return;}
        close();
    }
    function renderCampaigns(){
        const items=(data?.campaigns||[]).map(c=>node('li',{},node('button',{type:'button',class:'game-menu-card',disabled:!c.available||!!data?.error,
            onclick:()=>{campaignId=c.id;go('missions');}},
            node('strong',{text:c.title}),node('span',{text:c.description}),
            node('span',{class:'game-menu-meta',text:c.completed?'Completed':`${c.progress.completed} of ${c.progress.total} missions completed`}),
            ...(c.chapters||[]).map(ch=>node('span',{class:'game-menu-meta',text:`Chapter ${ch.number}: ${ch.title} · `+(ch.completed?'Complete':ch.available?`${percent(ch.progress.completed,ch.progress.total)}%`:'Locked')})),
            c.narrative_status==='draft'?node('span',{class:'game-menu-badge',text:'Story draft'}):null)));
        const list=items.length?node('ul',{class:'game-menu-list','data-menu-list':true},...items):node('p',{class:'game-menu-empty',text:paired?'No campaigns are installed.':'Campaigns appear once the companion service is connected.'});
        return [header('Campaigns',null,'Main menu'),statusLine(),list];
    }
    // Progress detail under an objective: milestones, play-style stages or the stages of a sequence.
    function objectiveDetail(o,a){
        const lines=[];
        if(o.milestones?.length)lines.push('Milestones: '+[...o.milestones,o.count].map(n=>(a&&a.progress>=n?'✓ ':'')+n).join(' · '));
        if(o.type==='style_stages'){
            if(a){
                for(const st of a.stages||[])lines.push(`${st.done?'✓':st.current?'▸':'○'} ${st.label} ${clock(st.seconds)} / ${clock(a.stage_seconds)}`+(st.current?' (current)':''));
                const left=Math.max(0,a.count*a.stage_seconds-a.elapsed);
                lines.push(`Stages ${a.progress} of ${a.count} · ${clock(a.elapsed)} done, ${clock(left)} to go · ${percent(a.elapsed,a.count*a.stage_seconds)}%`);
            } else lines.push(`${o.count} different play styles, ${clock(o.seconds)} each, no game on.`);
        }
        if(o.type==='stage_sequence'){
            for(const st of (a?.stages||o.stages)){
                const elapsed=a?st.elapsed:0;
                lines.push(`${st.done?'✓':st.current?'▸':'○'} ${st.label}: ${st.intensity}% · ${a?clock(elapsed)+' / ':''}${clock(st.seconds)}`+(st.current?' (current)':''));
            }
            if(a)lines.push(`${clock(a.elapsed)} of ${clock(a.total)} · ${clock(Math.max(0,a.total-a.elapsed))} to go · ${percent(a.elapsed,a.total)}%`);
        }
        if(o.after&&a&&!a.done)lines.push('Counts once the step above is done.');
        return lines.length?node('ul',{class:'mission-stages'},...lines.map(t=>node('li',{text:t}))):null;
    }
    function objectiveList(objectives,attempt){
        const live=attempt?Object.fromEntries(attempt.objectives.map(o=>[o.id,o])):{};
        return node('ul',{class:'mission-objectives'},...objectives.map(o=>{const a=live[o.id];const done=!!a?.done;
            return node('li',{class:done?'done':null},node('span',{'aria-hidden':'true',text:done?'✓':'○'}),
                node('div',{},node('span',{text:o.label+(a&&a.count?` (${a.progress}/${a.count})`:'')}),objectiveDetail(o,a)),
                node('span',{class:'sr-only',text:done?' — done':' — not done'}));}));
    }
    function renderMissions(){
        const c=campaign();if(!c)return renderCampaigns();
        const byId=Object.fromEntries(c.missions.map(m=>[m.id,m]));
        const chapters=Object.fromEntries((c.chapters||[]).map(ch=>[ch.number,ch]));
        let shown=null;
        const cards=c.missions.flatMap(m=>{
            const ch=chapters[m.chapter];
            const heading=ch&&ch.number!==shown?(shown=ch.number,node('li',{class:'mission-chapter','data-state':ch.completed?'completed':ch.available?'available':'locked'},
                node('h2',{text:`Chapter ${ch.number}: ${ch.title}`}),
                node('p',{text:ch.summary}),
                node('span',{class:'game-menu-meta',text:ch.completed?'Chapter complete · 100%':ch.available?`${ch.progress.completed} of ${ch.progress.total} missions · ${percent(ch.progress.completed,ch.progress.total)}%`:'Locked until the previous chapter is complete'}))):null;
            return [heading,missionCard(m,byId)].filter(Boolean);
        });
        return [header(c.title,c.description,'Campaigns'),statusLine(),
            live()?node('p',{class:'game-menu-status',text:'Stop the running session to start or switch missions.'}):null,
            node('ul',{class:'game-menu-list mission-list','data-menu-list':true},...cards)];
    }
    function missionCard(m,byId){{
            const locked=m.state==='locked';
            const needs=m.prerequisites.filter(p=>byId[p]?.state!=='completed').map(p=>byId[p]?.title||p);
            const action=m.state==='active'?'Continue':m.state==='completed'?(m.replay==='allowed'?'Replay':null):m.state==='available'?'Start mission':null;
            return node('li',{class:'mission-card','data-state':m.state},
                node('div',{class:'mission-card-art','aria-hidden':'true'},portrait(m.companion)&&!locked?node('img',{src:portrait(m.companion),alt:''}):node('span',{text:locked?'🔒':'✦'})),
                node('div',{class:'mission-card-body'},
                    node('p',{class:'mission-card-kicker',text:`Mission ${m.order} · ${name(m.companion)}`}),
                    node('h2',{text:m.title}),
                    node('span',{class:'game-menu-badge','data-state':m.state,text:STATE_LABEL[m.state]+(m.completions>1?` ×${m.completions}`:'')}),
                    m.narrative_draft&&!locked?node('span',{class:'game-menu-badge',text:'Story draft'}):null,
                    m.prerequisites.length&&!locked&&m.state!=='completed'?node('p',{class:'game-menu-meta',text:'After: '+m.prerequisites.map(p=>byId[p]?.title||p).join(', ')}):null,
                    node('p',{text:locked&&needs.length?`Complete ${needs.join(', ')} first.`:m.summary}),
                    locked?null:objectiveList(m.objectives,m.state==='active'?data.attempt:null),
                    m.rewards.length?node('p',{class:'mission-rewards',text:'Rewards: '+m.rewards.map(r=>(r.earned?'✓ ':'')+r.label).join(' · ')}):null),
                action?node('button',{type:'button',class:'accent-button',disabled:live()||!!data?.error,onclick:()=>startMission(m)},action):null);
        }
    }
    function speech(block){
        if(!block)return null;
        const src=portrait(block.speaker);
        return node('figure',{class:'mission-speech'},src?node('img',{src,alt:name(block.speaker)}):null,
            node('figcaption',{},node('strong',{text:name(block.speaker)}),...block.lines.map(line=>node('p',{text:line}))));
    }
    function renderBriefing(){
        const m=mission();if(!m)return renderMissions();
        return [header(m.title,`Mission ${m.order} · ${name(m.companion)}`,'Missions'),statusLine(),
            m.narrative_draft?node('p',{class:'game-menu-badge',text:'Story draft: this text is awaiting review.'}):null,speech(m.briefing),
            node('section',{class:'mission-brief'},node('h2',{text:'Objectives'}),objectiveList(m.objectives,data?.attempt),
                m.hints.length?node('ul',{class:'mission-hints'},...m.hints.map(h=>node('li',{text:h}))):null,
                m.settings_control?node('p',{class:'mission-hints',text:'AI Settings Control during this mission: '+m.settings_control.allowed.map(k=>SETTING_WORDS[k]||k).join(', ')+' only'
                    +(m.settings_control.then_allowed?`; later: ${m.settings_control.then_allowed.map(k=>SETTING_WORDS[k]||k).join(', ')}.`:'.')}):null,
                m.rewards.length?node('p',{class:'mission-rewards',text:'Rewards: '+m.rewards.map(r=>(r.earned?'✓ ':'')+r.label).join(' · ')}):null),
            node('div',{class:'game-menu-actions'},
                node('button',{type:'button',class:'accent-button',onclick:()=>{const r=selectCompanion(m.companion);if(r!==true){commandError=r||`Install ${name(m.companion)} first.`;render();return;}
                    postLines?.(m.briefing,'Mission briefing');close();}},`Begin with ${name(m.companion)}`),
                node('button',{type:'button',onclick:()=>{if(confirm(`Abandon ${m.title}? Completed missions and rewards are kept.`))send({version:1,type:'campaign',action:'abandon'});}},'Abandon mission'))];
    }
    function renderResults(){
        if(!result)return renderHome();
        const c=data?.campaigns?.find(x=>x.id===result.campaign);
        const next=(result.unlocked_missions||[]).map(id=>c?.missions.find(m=>m.id===id)).filter(Boolean);
        const chapter=result.chapter_complete;
        return [header(result.campaign_complete?'Campaign complete':chapter?`Chapter ${chapter.number} complete`:'Mission complete',chapter?`${result.title} · ${chapter.title}`:result.title,null),
            speech(result.completion),
            result.chapter_completion?speech(result.chapter_completion):null,
            result.campaign_complete&&result.campaign_completion?speech(result.campaign_completion):null,
            node('section',{class:'mission-brief'},node('h2',{text:'Objectives'}),objectiveList(result.objectives,{objectives:result.objectives}),
                node('h2',{text:result.earned.length?'Unlocked':'Rewards'}),
                node('ul',{class:'mission-hints'},...(result.earned.length?result.earned.map(r=>node('li',{text:r.label})):[node('li',{text:result.replay?'Replay: rewards were already earned.':'No new rewards.'})]),
                    ...next.map(m=>node('li',{text:`New mission: ${m.title}`}))),
                result.records?.calibrated_max_bpm?node('p',{text:`Saved maximum heart rate: ${result.records.calibrated_max_bpm} bpm`}):null),
            node('div',{class:'game-menu-actions'},
                node('button',{type:'button',class:'accent-button',disabled:live(),onclick:()=>{campaignId=result.campaign;go('missions');}},next[0]?`Next: ${next[0].title}`:'Campaign'),
                node('button',{type:'button',onclick:close},'Back to the session'))];
    }
    function render(){
        if(root.hidden)return;
        const parts={home:renderHome,campaigns:renderCampaigns,missions:renderMissions,briefing:renderBriefing,results:renderResults}[view]();
        panel.replaceChildren(...parts.filter(Boolean));
        panel.dataset.view=view;
        queueMicrotask(()=>(panel.querySelector('[data-menu-list] button:not([disabled]):not([aria-disabled]), .game-menu-actions button:not([disabled]), .game-menu-back')||panel.querySelector('button'))?.focus({preventScroll:true}));
    }
    function startMission(m){
        if(m.state==='active'){missionId=m.id;go('briefing');return;}
        pendingStart={campaign:campaignId,mission:m.id};commandError=null;
        send({version:1,type:'campaign',action:'start',campaign_id:campaignId,mission_id:m.id});
    }

    // ---- In-session banner
    const banner=node('section',{class:'mission-banner','aria-label':'Mission',hidden:true});
    const anchor=bannerHost.querySelector('.model-picker');if(anchor)anchor.after(banner);else bannerHost.prepend(banner);
    let toast=null;
    function renderBanner(){
        const active=data?.active,c=active&&data.campaigns.find(x=>x.id===active.campaign),m=c?.missions.find(x=>x.id===active.mission);
        if(!m&&!toast){banner.hidden=true;banner.replaceChildren();return;}
        banner.hidden=false;
        const parts=[];
        if(toast){
            const c2=data?.campaigns?.find(x=>x.id===toast.campaign);
            const next=(toast.unlocked_missions||[]).map(id=>c2?.missions.find(x=>x.id===id)?.title).filter(Boolean);
            parts.push(node('div',{class:'mission-toast',role:'status'},
                node('strong',{text:(toast.campaign_complete?'Campaign complete: ':toast.chapter_complete?`Chapter ${toast.chapter_complete.number} complete: `:'Mission complete: ')+toast.title}),
                node('span',{text:[...toast.earned.map(r=>r.label),...next.map(t=>'New mission: '+t)].join(' · ')||'Rewards were already earned.'}),
                node('span',{class:'game-menu-meta',text:live()?'Keep going as long as you like. Stop the session when you want to continue the campaign.':'Ready for what comes next.'}),
                node('div',{class:'game-menu-actions'},
                    node('button',{type:'button',disabled:live(),title:live()?'Stop the session first':null,onclick:()=>{result=toast;open('results');}},'Results'),
                    node('button',{type:'button',onclick:()=>{toast=null;renderBanner();}},'Dismiss'))));
        }
        if(m){
            const a=data.attempt;
            const notes=[];
            if(a&&!a.companion_selected)notes.push(`Progress counts with ${name(m.companion)} selected.`);
            if(a?.reset_reason==='session_ended')notes.push('The session ended before the mission was done. Counts start again with your next session.');
            if(data.notice)notes.push(data.notice);
            parts.push(node('div',{class:'mission-current'},
                node('p',{class:'eyebrow',text:`Mission ${m.order} · ${name(m.companion)}`}),node('strong',{text:m.title}),
                objectiveList(m.objectives,a),
                ...notes.map(t=>node('p',{class:'mission-note',text:t})),
                node('div',{class:'game-menu-actions'},
                    a&&!a.companion_selected?node('button',{type:'button',disabled:live(),onclick:()=>{const r=selectCompanion(m.companion);if(r!==true)alert(r);}},`Switch to ${name(m.companion)}`):null,
                    node('button',{type:'button',disabled:live(),title:live()?'Stop the session first':null,onclick:()=>{campaignId=active.campaign;missionId=m.id;open('briefing');}},'Briefing'))));
        }
        banner.replaceChildren(...parts);
    }

    // ---- Menu button in the dashboard bar
    const menuButton=node('button',{type:'button',class:'menu-button','data-main-menu':true,onclick:()=>{if(live())return;lastFocus=document.activeElement;open('home');}},'☰ Menu');
    const nav=document.querySelector('#companion-dashboard .companion-nav');
    nav?.querySelector('.companion-brand')?.after(menuButton);
    const syncLive=()=>{
        const isLive=live();
        menuButton.disabled=isLive;menuButton.title=isLive?'Stop the session to open the menu':'Main menu';
        // A session started some other way (gamepad, remote) is never hidden behind the menu.
        if(isLive&&!root.hidden)close();
    };
    const liveTimer=setInterval(()=>{const before=menuButton.disabled;syncLive();if(before!==menuButton.disabled)renderBanner();},500);

    open('home');
    return {
        connected(value){paired=value;if(!value&&pendingLeave){pendingLeave=false;commandError='The companion service disconnected, so the mission may still be in progress.';}if(value)send({version:1,type:'campaign',action:'get'});render();},
        receive(m){
            if(m.type==='campaign_state'){
                data=m;commandError=m.command_error||null;
                if(pendingStart&&m.active?.mission===pendingStart.mission&&!m.command_error){campaignId=pendingStart.campaign;missionId=pendingStart.mission;pendingStart=null;view='briefing';}
                else if(pendingStart&&m.command_error)pendingStart=null;
                if(view==='briefing'&&!m.active&&!m.command_error)view='missions';
                if(pendingLeave){pendingLeave=false;if(!m.active&&!m.command_error){render();renderBanner();close();return;}}
                render();renderBanner();
            } else if(m.type==='mission_result'){
                result=m;toast=m;
                postLines?.(m.completion,'Mission complete');
                if(m.chapter_completion)postLines?.(m.chapter_completion,`Chapter ${m.chapter_complete.number} complete`);
                if(m.campaign_complete&&m.campaign_completion)postLines?.(m.campaign_completion,'Campaign complete');
                renderBanner();
                if(!live()&&root.hidden){open('results');}
            } else if(m.type==='campaign_progress'){
                // The try's counts and stage clocks; the rest of the campaign view is unchanged.
                if(data&&m.active?.mission===data.active?.mission){data={...data,attempt:m.attempt,notice:m.notice};render();renderBanner();}
            } else if(m.type==='mission_milestone'){
                // A scripted progress line for the mission in progress (the observer sends each once per try).
                if(data?.active?.mission===m.mission)postLines?.(m.line,'Mission update');
            }
        },
        isOpen:()=>!root.hidden,
        destroy(){clearInterval(liveTimer);for(const type of ['keydown','keyup','keypress'])window.removeEventListener(type,guard,true);document.removeEventListener('focusin',refocus);root.remove();banner.remove();menuButton.remove();}
    };
}
