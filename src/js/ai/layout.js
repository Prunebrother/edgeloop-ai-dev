// SPDX-License-Identifier: AGPL-3.0-only
// Reparent existing controls, preserving their IDs, listeners and engine ownership.
export function mountLayout(chat,character) {
    // Stable upstream targets only. Upstream moves #sessionControlBar between
    // #sessionControlHome and the video HUD, and the Play Style/Endgame panels
    // between #sessionSetupHome and the player; those inner homes are never moved here.
    const need=id=>{const el=document.getElementById(id);if(!el)throw new Error('Companion layout target missing: #'+id);return el;};
    const devices=need('deviceBar'),player=need('playerSection'),cockpit=need('cockpit'),controls=need('sessionControlHome');
    const banner=need('disconnectBanner'),original=banner.parentElement;
    const heading=original.querySelector(':scope > header'),footer=original.querySelector(':scope > footer');
    if(!heading||!footer)throw new Error('Companion layout target missing: page header/footer');
    need('cockpitMain').firstElementChild?.classList.add('session-monitor');
    const shell=document.createElement('main');shell.id='companion-dashboard';shell.dataset.view='chat';
    shell.innerHTML=`<nav class="companion-nav" aria-label="Dashboard views"><span class="companion-brand">EDGE<span>LOOP</span> <small>COMPANION</small></span>
       <div role="group" aria-label="Views"><button data-view="session" aria-controls="session-panel">Session</button><button data-view="chat" aria-controls="ai-companion" aria-pressed="true">Chat</button><button data-view="character" aria-controls="character-panel">Character</button></div>
       <button data-emergency class="emergency">Emergency stop</button></nav>
       <div class="companion-columns"><section id="session-panel" aria-label="EdgeLoop session"><div class="session-scroll"></div><div class="session-transport"></div></section></div>`;
    const scroll=shell.querySelector('.session-scroll'),dock=shell.querySelector('.session-transport');
    const group=(title,nodes,open=false)=>{const d=document.createElement('details');d.className='session-group';d.open=open;
        const s=document.createElement('summary');s.textContent=title;d.append(s,...nodes);return d;};
    heading.classList.add('session-heading');
    scroll.append(heading,devices,player,cockpit,group('About EdgeLoop',[footer]));
    // The session buttons stay docked; upstream still re-homes the bar inside this container.
    dock.append(controls);
    const columns=shell.querySelector('.companion-columns');columns.append(chat,character);
    banner.setAttribute('role','alert');
    shell.insertBefore(banner,columns);
    // Anything upstream adds later at the top level stays reachable rather than lost.
    const rest=[...original.children];if(rest.length)scroll.append(group('More EdgeLoop controls',rest));
    original.replaceWith(shell);document.body.classList.add('companion-app');
    shell.querySelector('[data-emergency]').onclick=()=>{const stop=document.getElementById('sessionStopBtn');stop.dataset.safetyStop='true';stop.click();};
    const buttons=[...shell.querySelectorAll('[data-view]')];
    for(const button of buttons)button.onclick=()=>{const same=shell.dataset.view===button.dataset.view;
        shell.dataset.view=button.dataset.view==='character'&&same?'chat':button.dataset.view;
        for(const b of buttons)b.setAttribute('aria-pressed',String(b.dataset.view===shell.dataset.view));
    };
    // Keyboard-adjustable splitters are optional at wide desktop sizes.
    for(const [label,property,initial,min,max] of [['Session width','--session-width',27,23,34],['Character width','--character-width',33,25,36]]) {
        const input=document.createElement('input');input.type='range';input.min=min;input.max=max;input.value=initial;
        input.setAttribute('aria-label',label);input.className='column-width';
        input.oninput=()=>shell.style.setProperty(property,input.value+'%');
        const control=document.createElement('label');control.className='column-tuning';control.textContent=label.replace(' width','');control.append(input);shell.querySelector('.companion-nav').append(control);
    }
    // Recalculate canvas dimensions after structural movement or panel visibility changes.
    new ResizeObserver(()=>window.dispatchEvent(new Event('resize'))).observe(scroll);
    return shell;
}
