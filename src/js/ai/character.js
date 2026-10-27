// SPDX-License-Identifier: AGPL-3.0-only
import {MODEL_ARTWORK,resolveArtwork} from './artwork-manifest.js';
// Presentation-only: accepts explicit AI state, never physiological measurements.
// Not subscribed to telemetry or generation; future backend integration calls setState.
export class CharacterPresentation {
    constructor(host,manifest=MODEL_ARTWORK) {
        this.host=host;this.manifest=manifest;this.revision=0;
        host.innerHTML=`<header class="companion-heading"><div><p class="eyebrow">Character</p><h2 data-character-name>Your companion</h2></div><span class="expression" data-expression>Neutral</span></header>
          <div class="portrait-stage"><div class="portrait-placeholder"><div class="portrait-orbit" aria-hidden="true">✧</div><p>Room for a presence.</p><span>Character artwork will appear here</span></div><div data-art-layers></div></div>
          <footer class="character-caption"><span data-character-model>No model selected</span><span data-activity hidden></span><p>Artwork follows your selected model.</p></footer>`;
        this.setModel(null);
    }
    setModel(model) {this.model=model;this.setState({expression:'neutral'});}
    setState({expression='neutral',activity=null}={}) {
        const view=resolveArtwork(this.model,expression,this.manifest),revision=++this.revision;
        this.host.querySelector('[data-character-name]').textContent=this.model&&view.name==='Your companion'?this.model:view.name;
        this.host.querySelector('[data-expression]').textContent=view.expression[0].toUpperCase()+view.expression.slice(1);
        this.host.querySelector('[data-character-model]').textContent=this.model||'No model selected';
        const activityNode=this.host.querySelector('[data-activity]');
        activityNode.hidden=!['speaking','listening'].includes(activity);activityNode.textContent=activityNode.hidden?'':activity;
        const layers=this.host.querySelector('[data-art-layers]');
        const placeholder=this.host.querySelector('.portrait-placeholder');let candidate=0;
        if(!view.src){layers.replaceChildren();placeholder.hidden=false;return;}
        const img=new Image();img.alt=view.name+' · '+view.expression;img.className='character-art';
        img.onload=()=>{if(revision!==this.revision)return;layers.append(img);placeholder.hidden=true;requestAnimationFrame(()=>img.classList.add('visible'));
            setTimeout(()=>{if(revision===this.revision)layers.replaceChildren(img);},280);};
        img.onerror=()=>{if(revision!==this.revision)return;
            const fallback=view.sources[++candidate];
            if(fallback)img.src=fallback;
            else {layers.replaceChildren();placeholder.hidden=false;}};
        img.src=view.src;
    }
}
