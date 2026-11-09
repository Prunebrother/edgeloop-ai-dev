// SPDX-License-Identifier: AGPL-3.0-only
// Regression checks from the v0.7.0-rc1 review: card edits after a save, and dotted custom
// identities in Event Intelligence preferences. Modules are served from this checkout through
// request interception; no observer, network or device is used.
import {chromium} from 'playwright';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(new URL('../..',import.meta.url).pathname);
const assert=(x,m)=>{if(!x)throw Error(m);};
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('http://fixture.local/**',async route=>{
  const pathname=new URL(route.request().url()).pathname;
  if(pathname==='/')return route.fulfill({contentType:'text/html',body:'<div id="host"></div><div id="dialog"><div class="drawer-content"></div></div>'});
  return route.fulfill({contentType:pathname.endsWith('.json')?'application/json':'text/javascript',body:await readFile(path.join(root,pathname),'utf8')});
 });
 await page.goto('http://fixture.local/');

 const builder=await page.evaluate(async()=>{
  const {mountCharacterBuilder}=await import('/src/js/ai/character-builder.js');
  const sent=[];const b=mountCharacterBuilder(document.querySelector('#host'),{send:m=>{sent.push(structuredClone(m));return true;}});
  const world={id:'world',name:'World',setting:'An island',lore:'',rules:[]};
  const character={id:'wren',world:'world',name:'Wren',short_name:'Wren',personality:'Calm',voice:'Warm',relationship:'Friend',model:'example',deck:{shared:'lifecycle',cards:[{id:'one',theme:'story',brief:'Original brief',when:{},enabled:true}]}};
  const ok=(action,value)=>b.receive({type:'character_builder',action,ok:true,value:structuredClone(value)});
  b.receive({type:'character_builder',action:'get',kind:'character',ok:true,value:structuredClone(character)});
  b.receive({type:'character_builder',action:'get',kind:'world',ok:true,value:world});
  const lastSaved=()=>sent.filter(m=>m.action==='save_character').at(-1).character;
  const edit=(el,value)=>{if(el.type==='checkbox'){el.checked=value;el.dispatchEvent(new Event('change',{bubbles:true}));}else{el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));}};
  const enabledBox=()=>[...document.querySelectorAll('.builder-card input[type=checkbox]')].at(-1);
  // 1. Edits after a successful save reach the next save (brief and the Enabled checkbox).
  document.querySelector('[data-b-save]').click();ok('save_world',world);ok('save_character',{...character,revision:2});
  edit(document.querySelector('.builder-card textarea'),'Edited after save');edit(enabledBox(),false);
  document.querySelector('[data-b-save]').click();
  const afterSave=lastSaved();
  // 2. Edits made while a save is in flight are not overwritten by its response.
  edit(document.querySelector('.builder-card textarea'),'Typed during save');
  ok('save_world',world);ok('save_character',{...afterSave,revision:3});
  const visible=document.querySelector('.builder-card textarea').value;
  document.querySelector('[data-b-save]').click();
  const inFlight=lastSaved();
  return {afterSave:afterSave.deck.cards[0].brief,afterEnabled:afterSave.deck.cards[0].enabled,afterRevision:afterSave.revision,visible,
   inFlight:inFlight.deck.cards[0].brief,inFlightRevision:inFlight.revision};
 });
 assert(builder.afterSave==='Edited after save'&&builder.afterEnabled===false,'Card edits after a save were not sent: '+JSON.stringify(builder));
 assert(builder.afterRevision===2,'Saved revision was not adopted');
 assert(builder.visible==='Typed during save','Save response overwrote newer on-screen edits');
 assert(builder.inFlight==='Typed during save'&&builder.inFlightRevision===3,'Edit made during a save was lost: '+JSON.stringify(builder));

 const events=await page.evaluate(async()=>{
  const {mountEventSettings}=await import('/src/js/ai/event-settings.js');
  const sent=[];const s=mountEventSettings(document.querySelector('#dialog'),{send:m=>{sent.push(m);return true;}});
  const config={enabled:true,preset:'custom',proactive_interval_seconds:120,max_gap_seconds:12,detectors:{},preferences:{generic:{physiology:1,session:1,configuration:1,story:1},'custom.wren':{physiology:0,session:2,configuration:1,story:0}}};
  s.update({config,detectors:[],recent_events:[],active_identity:'custom.wren'});
  const field=k=>document.querySelector('[name="preferences.custom.wren.'+k+'"]');
  const shown={physiology:field('physiology').value,session:field('session').value,story:field('story').value};
  field('configuration').value='2';field('configuration').dispatchEvent(new Event('input',{bubbles:true}));
  document.querySelector('[data-event-form]').dispatchEvent(new Event('submit',{cancelable:true}));
  return {shown,preferences:sent.at(-1)?.config.preferences};
 });
 assert(JSON.stringify(events.shown)==='{"physiology":"0","session":"2","story":"0"}','Custom preferences were not reloaded: '+JSON.stringify(events.shown));
 assert(JSON.stringify(Object.keys(events.preferences).sort())==='["custom.wren","generic"]','Malformed preference identities: '+JSON.stringify(events.preferences));
 assert(JSON.stringify(events.preferences['custom.wren'])==='{"physiology":0,"session":2,"configuration":2,"story":0}','Custom preference not saved: '+JSON.stringify(events.preferences));
 assert(!errors.length,'Page errors: '+errors.join('; '));
 console.log('character-builder-regressions-browser: passed');
}finally{await browser.close();}
