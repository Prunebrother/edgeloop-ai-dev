// SPDX-License-Identifier: AGPL-3.0-only
// Presentation only. No telemetry values, prompts, memory, audio or device imports.
import {CHARACTER_MANIFEST,EXPRESSIONS,ACTIVITIES,resolveArtwork} from './artwork-manifest.js';
export const SESSION_REACTIONS=Object.freeze({...CHARACTER_MANIFEST.presentation.session_reactions});
// Only explicit self-description / stage direction. Arbitrary sentiment words,
// user feelings, numbers and physiological readings are never classifier inputs.
const CUES={
    attentive:/\b(?:I (?:listen closely|give you my full attention)|listens attentively)\b/i,
    curious:/\b(?:I tilt my head curiously|tilts? (?:her|my) head (?:with curiosity|curiously))\b/i,
    thoughtful:/\b(?:I pause thoughtfully|pauses? thoughtfully|I consider (?:that|this) carefully)\b/i,
    amused:/\b(?:I (?:chuckle softly|can't help but laugh)|chuckles? (?:softly|with amusement))\b/i,
    cheerful:/\b(?:I smile (?:warmly|brightly)|smiles? (?:warmly|brightly)|I'm delighted to (?:see|hear)|I(?:'m| am) (?:beaming|smiling (?:warmly|brightly)))\b/i,
    playful:/\b(?:I (?:give you a playful wink|grin mischievously)|winks? playfully|grins? mischievously)\b/i,
    excited:/\b(?:I beam with excitement|beams? with excitement|I can hardly contain my excitement)\b/i,
    surprised:/\b(?:I raise my eyebrows in surprise|raises? (?:her|my) eyebrows in surprise)\b/i,
    serious:/\b(?:I (?:adopt a serious expression|speak with quiet resolve)|(?:her|my) expression turns serious)\b/i,
    concerned:/\b(?:I frown with concern|frowns? with concern|I give you a concerned look)\b/i,
    relaxed:/\b(?:I (?:settle back comfortably|smile serenely)|settles? back comfortably)\b/i
};
export function classifyDialogue(text) {
    if(typeof text!=='string'||text.length>16000||/<think\b/i.test(text))return null;
    const safe=text.replace(/```[\s\S]*?```/g,'').replace(/"[^"\n]*"|“[^”\n]*”/g,'').slice(0,4000);
    const tones=Object.entries(CUES).filter(([,pattern])=>pattern.test(safe));
    return tones.length===1?tones[0][0]:null;
}
export class CharacterPresentationController {
    constructor(render,{now=()=>Date.now(),sessionReactions=SESSION_REACTIONS,cooldownMs=CHARACTER_MANIFEST.presentation.cooldown_ms,chatHoldMs=CHARACTER_MANIFEST.presentation.chat_hold_ms}={}) {
        Object.assign(this,{render,now,sessionReactions,cooldownMs,chatHoldMs});
        this.model=null;this.identity='generic';this.expression='neutral';this.activity='disconnected';this.connected=false;
        this.active=null;this.allowStarts=false;this.cancelled=new Set();this.seen=new Set();this.session=null;this.sequence=-1;
        this.chatUntil=0;this.lastReaction=-Infinity;this.previewState=null;this.emit();
    }
    emit(){this.render(this.previewState||{model:this.model,expression:this.expression,activity:this.activity});}
    bounded(set,value){set.add(value);if(set.size>128)set.delete(set.values().next().value);}
    select(model,history=[]) {
        this.cancel();const identity=resolveArtwork(model).id;
        if(identity!==this.identity)this.expression='neutral';
        this.model=model;this.identity=identity;
        const last=history.filter(m=>m.role==='assistant').at(-1);
        const tone=last&&classifyDialogue(last.content);if(tone)this.expression=tone;
        this.activity=this.connected?'idle':'disconnected';this.chatUntil=this.now()+this.chatHoldMs;this.emit();
    }
    connection(connected){this.connected=Boolean(connected);if(!connected){this.cancel();this.session=null;this.sequence=-1;this.seen.clear();}this.activity=connected?'idle':'disconnected';this.emit();}
    userMessage(){if(!this.connected)return;this.allowStarts=true;this.expression='attentive';this.activity='thinking';this.chatUntil=this.now()+this.chatHoldMs;this.emit();}
    start(id,model=this.model){
        if(!this.connected||!this.allowStarts||model!==this.model||typeof id!=='string'||this.cancelled.has(id)){if(typeof id==='string')this.bounded(this.cancelled,id);return false;}
        this.active={id,model};this.activity='thinking';this.emit();return true;
    }
    complete(id,text,model=this.model,metadata=null){
        if(!this.connected||!this.active||this.active.id!==id||model!==this.model||this.active.model!==model||this.cancelled.has(id))return false;
        const expression=metadata&&EXPRESSIONS.includes(metadata.expression)?metadata.expression:classifyDialogue(text);
        if(expression)this.expression=expression;
        this.active=null;this.allowStarts=false;this.activity='idle';this.chatUntil=this.now()+this.chatHoldMs;this.emit();return true;
    }
    cancel(){this.allowStarts=false;if(this.active)this.bounded(this.cancelled,this.active.id);this.active=null;this.activity=this.connected?'idle':'disconnected';this.emit();}
    // Only server-acknowledged F2.3 observed changes; no HR/speed input is read.
    sessionEvents(events,sequence,session){
        if(!this.connected||!Number.isSafeInteger(sequence)||!Array.isArray(events)||events.length>16||typeof session!=='string')return;
        if(this.session!==session){this.session=session;this.sequence=-1;this.seen.clear();}
        if(sequence<=this.sequence)return;this.sequence=sequence;
        for(const event of events){
            if(typeof event.id!=='string'||event.session_id!==session||this.seen.has(event.id))continue;
            this.bounded(this.seen,event.id);
            if(!Object.hasOwn(this.sessionReactions,event.kind))continue;
            const expression=this.sessionReactions[event.kind];if(!EXPRESSIONS.includes(expression))continue;
            if(event.kind!=='stop'&&(this.active||this.now()<this.chatUntil||this.now()-this.lastReaction<this.cooldownMs))continue;
            if(event.kind==='stop')this.cancel();
            this.expression=expression;this.lastReaction=this.now();this.emit();
        }
    }
    // Voice activities are explicit indicators only; never inferred or animated.
    setActivity(activity){if(ACTIVITIES.includes(activity)){this.activity=activity;this.emit();}}
    preview(value=null){this.previewState=value;this.emit();}
}
