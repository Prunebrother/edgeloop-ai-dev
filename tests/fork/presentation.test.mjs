// SPDX-License-Identifier: AGPL-3.0-only
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EXPRESSIONS,ACTIVITIES,resolveArtwork,MODEL_ARTWORK} from '../../src/js/ai/artwork-manifest.js';
import {CharacterPresentationController as Controller,classifyDialogue} from '../../src/js/ai/presentation-controller.js';
const evelyn='evelyn-lite-v1:latest',daisy='daisy-qwen35:latest';
const rig=options=>{let time=10000;const views=[];const c=new Controller(v=>views.push({...v}),{now:()=>time,...options});c.connection(true);c.select(evelyn);return {c,views,tick:n=>time+=n};};
test('canonical identities use exact aliases, not name prefixes or prototype properties',()=>{
    for(const model of ['evelyn-lite-v1:latest','evelyn-lite-candidate:latest','evelyn-qwen35-stable:latest','evelyn-qwen35:latest'])assert.equal(resolveArtwork(model).id,'evelyn');
    for(const model of ['daisy-qwen35:latest','daisy-v11:latest'])assert.equal(resolveArtwork(model).id,'daisy');
    for(const model of ['__proto__','evelyn-some-new-model:latest','qwen3:8b',null])assert.equal(resolveArtwork(model).id,'generic');
    assert.equal(Object.keys(MODEL_ARTWORK).length,15);
});
test('twelve expressions are independent from five activities, missing states fall back to neutral',()=>{
    assert.deepEqual(EXPRESSIONS,['neutral','attentive','curious','thoughtful','amused','cheerful','playful','excited','surprised','serious','concerned','relaxed']);
    assert.deepEqual(ACTIVITIES,['idle','thinking','listening','speaking','disconnected']);
    assert.equal(resolveArtwork(evelyn,'cheerful').src,'/Character_Art/Evelyn/Expressions/evelyn_happy.png');
    assert.deepEqual(resolveArtwork(evelyn,'relaxed').candidates,[{src:'/Character_Art/Evelyn/Expressions/evelyn_neutral.png',expression:'neutral'}]);
    assert.equal(resolveArtwork(evelyn,'speaking').expression,'neutral');
    assert.equal(resolveArtwork('unknown').src,null);
    const manifest={models:{'test:tag':'test'},characters:{test:{name:'Test',expressions:{neutral:'/neutral.png',playful:'/playful.webp'}}}};
    assert.deepEqual(resolveArtwork('test:tag','playful',manifest).sources,['/playful.webp','/neutral.png']);
    assert.equal(resolveArtwork('test:tag','playful',{models:{'test:tag':'test'},characters:{test:{name:'Test',expressions:{}}}}).src,null);
});
test('dialogue mapping requires explicit assistant self-expression, not arbitrary sentiment or physiology',()=>{
    assert.equal(classifyDialogue('*I smile warmly.* Welcome back.'),'cheerful');
    assert.equal(classifyDialogue("I'm beaming with a grin that could power a tractor."),'cheerful');
    assert.equal(classifyDialogue('*I give you a playful wink.* Hello.'),'playful');
    assert.equal(classifyDialogue('I pause thoughtfully. Let me consider that.'),'thoughtful');
    assert.equal(classifyDialogue('I frown with concern. I am here.'),'concerned');
    for(const text of ['You are excited with 140 BPM.','Your pulse is climbing.','I see you are concerned.','Happy to report the sensor is disconnected.',
        '"I smile warmly" is the sentence you wrote.','```I smile warmly```','<think>I smile warmly</think>Hello.', '*I smile warmly. I frown with concern.*'])assert.equal(classifyDialogue(text),null,text);
});
test('activity does not erase expression; accepted replies only and no token-level changes',()=>{
    const {c,views}=rig();c.userMessage();assert.equal(c.expression,'attentive');assert.equal(c.activity,'thinking');
    assert(c.start('one'));c.setActivity('listening');assert.equal(c.expression,'attentive');c.setActivity('speaking');assert.equal(c.expression,'attentive');
    assert(c.complete('one','*I give you a playful wink.*'));assert.equal(c.expression,'playful');assert.equal(c.activity,'idle');
    const n=views.length;assert(!c.complete('one','*I frown with concern.*'));assert.equal(views.length,n);
});
test('switching same-character models retains presentation; other characters reset and old generations cannot apply',()=>{
    const {c}=rig();c.userMessage();c.start('old');c.select(daisy);assert.equal(c.expression,'neutral');
    assert(!c.complete('old','*I frown with concern.*',evelyn));
    c.select(evelyn,[{role:'assistant',content:'*I give you a playful wink.*'}]);assert.equal(c.expression,'playful');
    c.select('evelyn-lite-candidate:latest');assert.equal(c.expression,'playful');
    c.select('unknown');assert.equal(c.identity,'generic');assert.equal(c.expression,'neutral');
});
test('cancel and disconnect invalidate generations, including late starts; reconnect starts a new sequence epoch',()=>{
    const {c,tick}=rig();c.userMessage();c.start('cancelled');c.cancel();assert(!c.complete('cancelled','*I smile warmly.*'));
    assert(!c.start('late'));c.connection(false);assert.equal(c.activity,'disconnected');assert(!c.complete('late','*I smile warmly.*'));
    c.connection(true);tick(9000);c.sessionEvents([{id:'first',kind:'milestone',session_id:'s'}],20,'s');assert.equal(c.expression,'cheerful');
    c.connection(false);c.connection(true);c.sessionEvents([{id:'new',kind:'stop',session_id:'s'}],0,'s');assert.equal(c.expression,'neutral');
});
test('verified event adapter is bounded/deduplicated, chat has priority and stop bypasses debounce',()=>{
    const {c,tick}=rig();tick(9000);const event=(id,kind)=>({id,kind,session_id:'s'});
    c.sessionEvents([event('1','milestone')],1,'s');assert.equal(c.expression,'cheerful');
    c.sessionEvents([event('1','stop')],2,'s');assert.equal(c.expression,'cheerful');
    c.sessionEvents([event('2','pause')],3,'s');assert.equal(c.expression,'cheerful');
    tick(6001);c.sessionEvents([event('3','pause')],4,'s');assert.equal(c.expression,'attentive');
    c.userMessage();c.start('active');c.sessionEvents([event('4','milestone')],5,'s');assert.equal(c.expression,'attentive');
    c.sessionEvents([event('5','stop')],6,'s');assert.equal(c.expression,'neutral');assert.equal(c.active,null);
    assert(!c.complete('active','*I smile warmly.*'));
    c.sessionEvents([event('6','milestone')],5,'s');assert.equal(c.expression,'neutral');
});
test('session policy can be disabled; physiological fields and unrelated events never select emotion',()=>{
    const {c,tick}=rig({sessionReactions:{}});tick(10000);
    c.sessionEvents([{id:'1',kind:'milestone',session_id:'s',hr:250}],1,'s');assert.equal(c.expression,'neutral');
    const other=rig();other.tick(10000);other.c.sessionEvents([{id:'2',kind:'hr_rising',session_id:'s',hr:250}],1,'s');assert.equal(other.c.expression,'neutral');
});
test('development preview overlays rendering only and restores live state',()=>{
    const {c,views}=rig();const state=c.expression;c.preview({model:daisy,expression:'excited',activity:'speaking'});assert.equal(views.at(-1).expression,'excited');assert.equal(c.expression,state);assert.equal(c.model,evelyn);c.preview();assert.equal(views.at(-1).model,evelyn);
});
