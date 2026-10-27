// SPDX-License-Identifier: AGPL-3.0-only
import {Capture} from './snapshot.js';
import {ReadOnlyConnection} from './connection.js';
import {CharacterPresentation} from './character.js';
import {mountLayout} from './layout.js';
export function mountCompanion({refreshObservation=()=>{}}={}) {
    const capture=new Capture();
    const panel=document.createElement('section');panel.id='ai-companion';panel.dataset.paired='false';panel.setAttribute('aria-label','AI conversation');
    // Static markup only. Server and model text is always assigned with textContent.
    panel.innerHTML=`<header class="companion-heading"><div><p class="eyebrow">AI companion · local & private</p><h2 data-name>Make yourself at home.</h2></div><span class="model-activity" data-activity-state="offline" role="status" aria-live="polite"><span class="activity-light" aria-hidden="true"></span><span data-activity-label>Offline</span></span></header>
      <div class="connection-strip"><span data-status role="status">AI disabled</span><button data-disconnect type="button" hidden>Disconnect</button></div>
      <form data-setup class="connection-setup"><h3>Connect your companion</h3><p>Pair with your local AI service to begin. EdgeLoop works independently.</p>
        <label>Companion service (WebSocket)<input data-url value="ws://127.0.0.1:8768/observe" autocomplete="off" spellcheck="false"></label>
        <label>Pairing token<input data-token type="password" autocomplete="off" required minlength="32" maxlength="128"></label>
        <button data-connect class="accent-button" type="submit">Pair local AI</button></form>
      <div class="model-picker"><label>Ollama model<select data-model aria-label="Installed model" disabled><option value="" disabled>Pair to discover models</option></select></label><button data-select type="button" disabled>Switch model</button><button data-refresh type="button" disabled aria-label="Refresh installed models">↻</button></div>
      <div class="model-controls"><button data-thinking type="button" aria-pressed="false" disabled>Thinking: unknown</button><span data-thinking-hint>Choose a model to see its thinking setting.</span></div>
      <div class="ai-health"><span data-selected>No AI model active</span><span data-ollama>Ollama not checked</span><span data-endpoint>Ollama endpoint pending</span><span data-telemetry>Telemetry not connected</span></div>
      <div class="conversation-scroll" data-history role="log" aria-label="Conversation history" aria-live="off" tabindex="0"><div class="conversation-empty" data-empty><span aria-hidden="true">✧</span><h3>A little space to connect.</h3><p>Your conversation lives here.<br>Choose a local model and say hello.</p></div></div>
      <button data-latest class="jump-latest" type="button" hidden>Jump to latest ↓</button>
      <p data-error class="chat-error" role="alert" hidden></p><p data-progress role="status" class="chat-progress"></p>
      <form data-chat class="chat-composer"><label for="companion-message">Message your companion</label><textarea id="companion-message" data-text maxlength="2000" rows="3" placeholder="What’s on your mind?" disabled></textarea><div class="composer-actions"><span>Enter to send · Shift+Enter for a new line</span><button data-cancel type="button" hidden>Cancel generation</button><button data-send class="accent-button" type="submit" disabled>Send ↑</button></div></form>
      <p class="read-only-note">Read-only companion · Session and safety stay with EdgeLoop</p>`;
    const artwork=document.createElement('aside');artwork.id='character-panel';artwork.setAttribute('aria-label','Character artwork');
    const character=new CharacterPresentation(artwork);mountLayout(panel,artwork);
    const el=key=>panel.querySelector(`[data-${key}]`);
    let selected=null,current=null,pending=false,follow=true,paired=false,changing=false,thinking=null,supportsThinking=false;
    let discovered=new Set();
    const scroll=()=>{if(follow)el('history').scrollTop=el('history').scrollHeight;};
    el('history').onscroll=()=>{follow=el('history').scrollHeight-el('history').clientHeight-el('history').scrollTop<60;el('latest').hidden=follow;};
    el('latest').onclick=()=>{follow=true;el('latest').hidden=true;scroll();};
    // Preserve the reader's position while tokens arrive or portrait assets change.
    new ResizeObserver(scroll).observe(el('history'));
    const activity=(state,label)=>{const badge=panel.querySelector('[data-activity-state]');badge.dataset.activityState=state;el('activity-label').textContent=label;};
    const controls=()=>{
        el('send').disabled=!selected||pending||changing;el('text').disabled=!selected||changing;
        el('select').disabled=!paired||pending||changing||!discovered.has(el('model').value);el('model').disabled=!paired||pending||changing;
        el('thinking').disabled=!discovered.has(selected)||!selected||!supportsThinking||thinking===null||pending||changing;
        el('thinking').setAttribute('aria-pressed',String(thinking===true));
        el('thinking').textContent=thinking===null?'Thinking: unknown':supportsThinking?'Thinking: '+(thinking?'On':'Off'):'Thinking unavailable';
        el('thinking-hint').textContent=!selected?'Choose a model to see its thinking setting.':!supportsThinking?'This model does not advertise thinking support.':thinking?'Reasoning enabled before the reply.':'Direct reply mode.';
    };
    const resting=()=>activity(changing?'loading':selected?'ready':paired?'connected':'offline',changing?'Applying model…':selected?'Ready':paired?'Select a model':'Offline');
    const busy=(value,label='Generating…')=>{pending=value;el('cancel').hidden=!value;el('progress').textContent=value?label:'';el('history').setAttribute('aria-busy',String(value));controls();if(value)activity('working',thinking?'Working · thinking on':'Working · thinking off');else resting();};
    const error=text=>{el('error').textContent=text;el('error').hidden=!text;};
    const line=(role,text)=>{el('empty')?.remove();const node=document.createElement('article');node.className='message message-'+role;
        const name=document.createElement('span');name.className='message-author';name.textContent=role==='user'?'You':selected||'Companion';
        const body=document.createElement('div');body.className='message-content';body.textContent=text;node.append(name,body);el('history').append(node);
        while(el('history').children.length>64)el('history').firstElementChild.remove();scroll();return {node,body};};
    const finish=()=>{if(current){if(!current.text)current.node.remove();current=null;}busy(false);};
    const connection=new ReadOnlyConnection({onStatus:text=>{
        const connected=!!connection.epoch;paired=connected;panel.dataset.paired=String(connected);el('status').textContent=text;
        el('setup').hidden=connected;el('disconnect').hidden=!connection.enabled;
        for(const key of ['model','select','refresh'])el(key).disabled=!connected;
        if(!connected){discovered.clear();selected=null;changing=false;thinking=null;supportsThinking=false;finish();el('text').disabled=true;el('send').disabled=true;el('selected').textContent='No active AI connection';el('telemetry').textContent='Telemetry disconnected';el('ollama').textContent='Ollama not checked';}controls();resting();
    },onMessage:m=>{
        if(m.type==='models'){
            el('model').replaceChildren();for(const entry of m.models.slice(0,128)){const o=document.createElement('option');o.value=entry.name;o.textContent=entry.name;el('model').append(o);}
            const names=m.models.slice(0,128).map(entry=>entry.name);discovered=new Set(names);
            if(!names.length){const o=document.createElement('option');o.value='';o.textContent='No installed models';o.disabled=true;el('model').append(o);}
            if(m.ollama_url)el('endpoint').textContent='Ollama: '+m.ollama_url;el('model').value=names.includes(selected)?selected:names.includes(m.selected)?m.selected:(names[0]||'');
            el('ollama').textContent=names.length?'Ollama connected · '+names.length+' models':'Ollama connected · no installed models';
            controls();
        } else if(m.type==='model_selected'){
            const sameModel=selected===m.model;changing=false;finish();selected=m.model;thinking=typeof m.thinking==='boolean'?m.thinking:null;supportsThinking=m.supports_thinking===true;el('selected').textContent='Active: '+m.model;el('name').textContent=m.model;el('model').value=m.model;
            if(!sameModel){character.setModel(m.model);el('history').replaceChildren();follow=true;
                for(const item of m.history||[])line(item.role==='user'?'user':'assistant',item.content);}
            el('text').disabled=false;busy(false);error('');
        } else if(m.type==='response_start'){
            current?.node.remove();current={id:m.id,...line('assistant',''),text:''};busy(true);
        } else if(m.type==='response_delta'&&current?.id===m.id){current.text+=m.text;current.body.textContent=current.text;activity('responding','Responding');scroll();}
        else if(m.type==='speech'){
            if(current?.id===m.id){current.body.textContent=m.text;current=null;}else line('assistant',m.text);
            busy(false);scroll();
        } else if(m.type==='speech_cancel'){finish();}
        else if(m.type==='response_suppressed'){finish();el('progress').textContent='Companion is staying quiet.';}
        else if(m.type==='observation_ack')el('telemetry').textContent=m.accepted?'Authoritative telemetry connected · sequence '+m.sequence:'Telemetry awaiting fresh update';
        else if(m.type==='telemetry_status')el('telemetry').textContent='Telemetry stale · session state unavailable to AI';
        else if(['ai_error','conversation_error','protocol_error'].includes(m.type)){changing=false;if(m.ollama_url)el('endpoint').textContent='Ollama: '+m.ollama_url;
            if(m.code==='discovery_unavailable'){discovered.clear();const o=document.createElement('option');o.value='';o.disabled=true;o.textContent='Ollama unavailable';el('model').replaceChildren(o);}
            if(m.selection_failed&&!m.active){selected=null;thinking=null;supportsThinking=false;}finish();error((m.detail||'AI unavailable')+(m.errors?.length?' · '+m.errors.map(e=>e.path.join('.')+': '+e.code).join(', '):''));activity('error',selected?'Ready · last request failed':'AI unavailable');if(m.type==='ai_error')el('ollama').textContent='Ollama request unavailable';}
    }});
    el('setup').onsubmit=e=>{e.preventDefault();error('');try{connection.connect(el('url').value,el('token').value);}catch(e){error(e.message);}finally{el('token').value='';}};
    el('disconnect').onclick=()=>connection.disconnect();
    el('refresh').onclick=()=>connection.send({version:1,type:'list_models'});
    const selectModel=(model,requestedThinking)=>{
        if(pending||changing)return;
        if(!discovered.has(model)){error('Refresh the model list and choose an installed model.');return;}
        const message={version:1,type:'select_model',selection:{model}};
        if(typeof requestedThinking==='boolean')message.thinking=requestedThinking;
        if(connection.send(message)){error('');changing=true;el('progress').textContent='Applying model settings…';controls();resting();}
    };
    el('select').onclick=()=>selectModel(el('model').value);
    el('thinking').onclick=()=>{if(selected&&supportsThinking)selectModel(selected,!thinking);};
    el('cancel').onclick=()=>{if(connection.send({version:1,type:'cancel_generation'})){finish();el('progress').textContent='Generation cancelled.';}};
    el('chat').onsubmit=e=>{e.preventDefault();if(!selected||pending||changing)return;
        const text=el('text').value.trim();if(text&&connection.send({version:1,type:'chat',model:selected,text})){follow=true;line('user',text);el('text').value='';error('');busy(true,'Waiting for companion…');}};
    el('text').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();el('chat').requestSubmit();}};
    // Original idle/paused sessions need no engine ticks. Refresh only the read-only projection.
    const observationTimer=setInterval(()=>{if(connection.epoch){try{refreshObservation();}catch{ /* Optional AI stays isolated. */ }}},1000);
    window.addEventListener('pagehide',()=>{clearInterval(observationTimer);connection.disconnect();});
    return (state,devices)=>connection.observe(capture.project(state,devices));
}
