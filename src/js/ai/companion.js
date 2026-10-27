// SPDX-License-Identifier: AGPL-3.0-only
import {Capture} from './snapshot.js';
import {ReadOnlyConnection} from './connection.js';
export function mountCompanion() {
    const capture=new Capture();
    const panel=document.createElement('details');panel.id='ai-companion';
    panel.style.cssText='position:relative;margin:1rem;padding:1rem;background:#101827;color:#e5e7eb;border:1px solid #64748b;border-radius:.7rem;z-index:20;font:14px system-ui';
    // Static markup only. Every server/model-derived string uses textContent.
    panel.innerHTML=`<summary>Optional local AI companion · read-only</summary>
      <p>Original EdgeLoop controls own the session. AI cannot change devices or session state.</p>
      <label>AI service <input data-url value="ws://127.0.0.1:8768/observe" style="color:#111"></label>
      <label>Pairing token <input data-token type="password" autocomplete="off" style="color:#111"></label>
      <button data-connect type="button">Enable AI connection</button> <button data-disconnect type="button">Disable AI</button>
      <p data-status role="status">AI disabled</p><p data-telemetry>Telemetry not connected</p>
      <label>Installed model <select data-model style="color:#111"></select></label>
      <button data-select type="button">Switch model</button> <span data-selected>No AI model active</span>
      <div data-history role="log" aria-live="polite" style="max-height:18rem;overflow:auto;white-space:pre-wrap;margin:1rem 0"></div>
      <form data-chat><label>Message <input data-text maxlength="2000" required style="color:#111;width:65%"></label><button type="submit">Send</button></form>
      <p data-ack>No control requests: F2 is read-only.</p>`;
    document.body.append(panel);
    const el=key=>panel.querySelector(`[data-${key}]`);let selected=null,current=null;
    const line=text=>{const p=document.createElement('p');p.textContent=text;el('history').append(p);while(el('history').children.length>64)el('history').firstElementChild.remove();return p;};
    const connection=new ReadOnlyConnection({onStatus:text=>{el('status').textContent=text;if(!connection.epoch){current?.node.remove();current=null;selected=null;el('selected').textContent='No active AI connection';el('telemetry').textContent='Telemetry disconnected';}},onMessage:m=>{
        if(m.type==='models'){
            el('model').replaceChildren();for(const entry of m.models.slice(0,128)){const o=document.createElement('option');o.value=entry.name;o.textContent=entry.name;el('model').append(o);}
            const names=m.models.slice(0,128).map(entry=>entry.name);
            el('model').value=names.includes(m.selected)?m.selected:(names[0]||'');
        } else if(m.type==='model_selected'){
            selected=m.model;el('selected').textContent='Active: '+m.model;el('history').replaceChildren();current=null;
            for(const item of m.history||[])line(item.role+': '+item.content);
        } else if(m.type==='response_start'){current?.node.remove();current={id:m.id,node:line((m.responder?.model||selected||'AI')+': '),text:''};}
        else if(m.type==='response_delta'&&current?.id===m.id){current.text+=m.text;current.node.textContent=(selected||'AI')+': '+current.text;}
        else if(m.type==='speech'){
            if(current?.id===m.id){current.node.textContent=(selected||'AI')+': '+m.text;current=null;}
            else line((m.source==='safety'?'Observed safety':'AI')+': '+m.text);
        } else if(m.type==='speech_cancel'){current?.node.remove();current=null;}
        else if(m.type==='observation_ack')el('telemetry').textContent=m.accepted?'Authoritative telemetry connected · sequence '+m.sequence:'Telemetry awaiting fresh update';
        else if(m.type==='telemetry_status')el('telemetry').textContent='Telemetry stale; current session state unavailable to AI';
        else if(['ai_error','conversation_error','protocol_error'].includes(m.type))line(m.detail||'AI unavailable');
    }});
    el('connect').onclick=()=>{try{connection.connect(el('url').value,el('token').value);el('token').value='';}catch(e){el('status').textContent=e.message;}};
    el('disconnect').onclick=()=>connection.disconnect();
    el('select').onclick=()=>{selected=null;connection.send({version:1,type:'select_model',selection:{model:el('model').value}});};
    el('chat').onsubmit=e=>{e.preventDefault();if(!selected){line('Select an installed model before sending.');return;}
        const text=el('text').value.trim();if(text&&connection.send({version:1,type:'chat',model:selected,text})){line('You: '+text);el('text').value='';}};
    window.addEventListener('pagehide',()=>connection.disconnect());
    return (state,devices)=>connection.observe(capture.project(state,devices));
}
