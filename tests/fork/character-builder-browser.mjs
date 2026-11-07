// SPDX-License-Identifier: AGPL-3.0-only
// Character Builder end to end in the real app: isolated observer, mocked Ollama and Handy,
// the app's Manual Simulator for heart rate. Create, save, validate, preview, activate, talk,
// let the Director draw a custom card, reopen, and switch back to a built-in companion.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {copyFile,mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {claimPorts,ownedReady,isolatedEnv,guardBrowser} from './fixture-isolation.mjs';
const root=path.resolve(new URL('../..',import.meta.url).pathname);
const output=process.env.CHARACTER_BUILDER_BROWSER_REPORT||'/tmp/edgeloop-character-builder-browser';
const uiPort=8840,aiPort=8848,ui=`http://127.0.0.1:${uiPort}`,ai=`http://127.0.0.1:${aiPort}`;
const python=process.env.EDGELOOP_TEST_PYTHON||path.join(root,'.venv/bin/python');
const fixture=path.join(root,'tests/fixtures/character-builder');
const BASE='huihui_ai/qwen3.5-abliterated:9b',DAISY='daisy-narrative-f29-v014:latest';
const report={passed:false,steps:[],screenshots:[],physical_devices:'Denied; Handy HTTP intercepted'};
const children=[];const errors=[];let browser,page;
const assert=(v,m)=>{if(!v)throw Error(m);};
const json=async url=>(await fetch(ai+url)).json();
async function shot(name){await page.screenshot({path:path.join(output,name),fullPage:false});report.screenshots.push(name);}
try{
 await mkdir(output,{recursive:true});
 const world=JSON.parse(await readFile(path.join(fixture,'world-saltglass.json'),'utf8'));
 const wren=JSON.parse(await readFile(path.join(fixture,'character-wren.json'),'utf8'));
 await claimPorts(uiPort,aiPort);
 const env={EDGELOOP_FIXTURE_UI_PORT:String(uiPort),EDGELOOP_FIXTURE_OBSERVER_PORT:String(aiPort),PYTHONPATH:root};
 for(const [command,args,extra] of [['python3',['tools/serve_local.py',String(uiPort)],{}],[python,['tests/fork/character_builder_browser_service.py'],env]])
  children.push(spawn(command,args,{cwd:root,env:{...isolatedEnv(),...extra},stdio:'ignore'}));
 await ownedReady(ui+'/',children);await ownedReady(ai+'/health',children);
 browser=guardBrowser(await chromium.launch(),[uiPort,aiPort]);
 const context=await browser.newContext({viewport:{width:1600,height:1000}});
 await context.addInitScript(()=>{const no=()=>Promise.reject(new DOMException('Mocked-device test','NotFoundError'));Object.defineProperty(navigator,'bluetooth',{value:{requestDevice:no},configurable:true});Object.defineProperty(navigator,'serial',{value:{requestPort:no,getPorts:async()=>[]},configurable:true});});
 await context.route('**/api/handy/v2/**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(route.request().url().endsWith('/connected')?{connected:true}:route.request().url().endsWith('/info')?{fwVersion:'3.2.3',model:'Handy 1.1'}:{result:0})}));
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(ui+'/');await page.locator('#ageConfirmBtn').click();await page.locator('#wizardOverlay').waitFor({state:'visible'});await page.locator('#wizardSkipBtn').click();await page.locator('#companion-dashboard').waitFor();
 // A running simulated session: Manual Simulator heart rate and a mocked Handy.
 await page.locator('#cardBle').click();await page.getByRole('button',{name:/manual simulator/i}).click();await page.locator('#modalSimHrSlider').evaluate(el=>{el.value='96';el.dispatchEvent(new Event('input',{bubbles:true}));});await page.locator('#modalEngageSimBtn').click();if(await page.locator('#modalCloseBtn').isVisible())await page.locator('#modalCloseBtn').click();
 await page.locator('#cardHandy').click();await page.locator('#modalHandyInput').fill('BUILDER-MOCK-ONLY');await page.locator('#modalHandyConnectBtn').click();await page.waitForTimeout(600);if(await page.locator('#modalCloseBtn').isVisible())await page.locator('#modalCloseBtn').click();
 await page.locator('#sessionPlayPauseBtn').click();
 await page.waitForFunction(async()=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='RUNNING';});
 await page.locator('[data-url]').fill(`ws://127.0.0.1:${aiPort}/observe`);await page.locator('[data-token]').fill('browser-fixture-token-'+'x'.repeat(32));await page.locator('[data-connect]').click();
 await page.locator(`[data-model] option[value="${DAISY}"]`).waitFor({state:'attached'});
 report.steps.push('Simulated session running; paired with the isolated observer');

 // Open the builder; drop the portrait into the art folder it names, then reopen.
 const builder=page.locator('[data-character-builder]');
 await builder.locator('summary').click();
 const folderText=await builder.locator('[data-b-art-folder]').filter({hasText:'Put portrait'}).textContent();
 const folder=folderText.match(/ in (.+) and reopen/)[1];
 await copyFile(path.join(fixture,'wren.png'),path.join(folder,'wren.png'));
 await builder.locator('summary').click();await builder.locator('summary').click();
 await builder.locator('[data-b-art] option[value="wren.png"]').waitFor({state:'attached'});
 // World and character, typed through the editor.
 for(const key of ['id','name','setting','lore'])await builder.locator(`[data-w="${key}"]`).fill(world[key]);
 await builder.locator('[data-w="rules"]').fill(world.rules.join('\n'));
 for(const key of ['id','name','short_name','personality','voice','relationship','model'])await builder.locator(`[data-c="${key}"]`).fill(String(wren[key]));
 await builder.locator('[data-c="age"]').fill(String(wren.age));
 await builder.locator('[data-b-art]').selectOption('wren.png');
 // A small deck: two tide-lore cards against one dry-tease card, and one malformed card.
 const cards=[wren.deck.cards[0],wren.deck.cards[1],wren.deck.cards[4],{id:'bad-card',theme:'oops',brief:'Raise the speed now and tell them.',when:{}}];
 for(let i=1;i<cards.length;i++)await builder.locator('[data-b-add]').click();
 const cardBoxes=builder.locator('.builder-card');
 for(const [i,card] of cards.entries()){
  const box=cardBoxes.nth(i);
  await box.getByLabel('Card ID').fill(card.id);await box.getByLabel('Theme').fill(card.theme);await box.getByLabel('Brief for the model').fill(card.brief);
  if(card.when.min_seconds!=null)await box.getByLabel('From second').fill(String(card.when.min_seconds));
 }
 await builder.locator('[data-b-preview]').click();
 await builder.locator('[data-b-errors] li').first().waitFor();
 const shown=await builder.locator('[data-b-errors]').textContent();
 assert(/cards › 3 › brief: Cards are dialogue and story briefs/.test(shown),'Malformed card error not shown: '+shown);
 assert(await builder.locator('[data-b-activate]').isDisabled(),'Activate enabled with errors');
 await shot('validation-error.png');report.steps.push('A card asking to change the speed is rejected with its path; Activate stays disabled');
 await cardBoxes.nth(3).getByRole('button',{name:'Remove card'}).click();
 await builder.locator('[data-b-preview]').click();
 await builder.locator('[data-b-preview-out] h4').waitFor();
 const heading=await builder.locator('[data-b-preview-out] h4').textContent();
 assert(heading.startsWith('Wren Calloway · The Saltglass Reach · revision 1'),'Preview heading: '+heading);
 assert((await builder.locator('[data-b-preview-out]').textContent()).includes('tide_lore ×2, dry_tease ×1')||(await builder.locator('[data-b-preview-out]').textContent()).includes('dry_tease ×1, tide_lore ×2'),'Theme weights missing');
 await page.waitForFunction(()=>document.querySelector('.builder-portrait')?.naturalWidth>0);
 await builder.locator('[data-b-preview-out] details summary').click();
 await shot('preview.png');report.steps.push('Saved locally (revision 1); preview shows persona, deck, theme weights, shared lifecycle and portrait');

 await builder.locator('[data-b-activate]').click();
 await page.waitForFunction(()=>document.querySelector('[data-selected]').textContent.startsWith('Active: Wren Calloway (custom)'));
 await page.waitForFunction(()=>{const h=document.querySelector('#character-panel');return h.dataset.character==='custom.wren-calloway'&&h.querySelector('img')?.naturalWidth>0;});
 assert((await page.locator('#character-panel [data-character-name]').textContent())==='Wren Calloway','Character name not shown');
 const scope=await json('/fixture/scope');assert(scope.scope.endsWith(`${BASE}#character=wren-calloway`),'Scope: '+scope.scope);
 report.steps.push('Activated: portrait, name and a separate memory scope for the custom character');

 await page.locator('[data-text]').fill('Where am I?');await page.locator('[data-text]').press('Enter');
 await page.waitForFunction(()=>document.querySelector('[data-history]').textContent.includes('Stillwater light, Saltglass Reach'));
 let chats=await json('/fixture/chats');let last=chats.at(-1);
 assert(last.system.startsWith('You are Wren Calloway')&&!/Daisy|Cloverfield/.test(last.system),'Persona did not replace the model identity');
 report.steps.push('User chat runs on the custom persona; the model\'s built-in Daisy identity never reaches the request');

 await fetch(ai+'/fixture/fast-deck',{method:'POST'});
 // The shared opening card plays first; the custom cards need 60 s of running time.
 await page.waitForFunction(()=>document.querySelector('[data-history]').textContent.includes('Logged: the tide turns'),null,{timeout:30000});
 chats=await json('/fixture/chats');
 assert(chats.some(c=>c.last.includes('A MOMENT TO SPEAK')&&c.last.includes('Mark the start in your own voice')),'Shared opening card did not play first');
 report.steps.push('Shared lifecycle opening card played in Wren\'s voice');
 await page.evaluate(async()=>{const {state}=await import('/src/js/state.js');state.sessionSeconds=Math.max(state.sessionSeconds,120);});
 let card=null;
 for(let i=0;i<60&&!card;i++){
  await page.waitForTimeout(500);
  card=(await json('/fixture/chats')).find(c=>c.last.includes('A MOMENT TO SPEAK')&&cards.slice(0,3).some(x=>c.last.includes(x.brief)));
 }
 assert(card,'No custom card brief reached the model');
 await page.waitForFunction(()=>[...document.querySelectorAll('.message-assistant')].filter(n=>n.textContent.includes('Logged:')).length>=2,null,{timeout:15000});
 const used=cards.slice(0,3).find(x=>card.last.includes(x.brief));
 report.steps.push(`Director drew custom card "${used.id}" (${used.theme}) in the simulated session and the reply was shown`);
 await shot('custom-card-dialogue.png');

 // Reopen from the saved library.
 await builder.locator('[data-b-open]').selectOption('wren-calloway');
 await builder.locator('[data-c="name"]').fill('');
 await builder.locator('[data-b-load]').click();
 await page.waitForFunction(()=>document.querySelector('[data-c="name"]').value==='Wren Calloway'&&document.querySelector('[data-w="name"]').value==='The Saltglass Reach');
 assert(await builder.locator('.builder-card').count()===3,'Reopened deck has the wrong card count');
 report.steps.push('Reopened the saved character and its world from the local library');

 // Back to a built-in companion through the normal model picker.
 await page.locator('[data-model]').selectOption(DAISY);await page.locator('[data-select]').click();
 await page.waitForFunction(m=>document.querySelector('[data-selected]').textContent==='Active: '+m,DAISY);
 await page.waitForFunction(()=>document.querySelector('#character-panel').dataset.character==='daisy');
 await page.locator('[data-text]').fill('Hello again');await page.locator('[data-text]').press('Enter');
 await page.waitForFunction(()=>document.querySelector('[data-history]').textContent.includes('Cloverfield Farm says hello.'));
 last=(await json('/fixture/chats')).at(-1);
 assert(last.system.startsWith('You are Daisy Mae Harper')&&!last.system.includes('Wren'),'Built-in identity not restored');
 assert(!(await page.locator('[data-history]').textContent()).includes('Stillwater'),'Custom character history leaked into the built-in companion');
 await shot('back-to-builtin.png');report.steps.push('Switched back to Daisy: built-in identity, portrait and an empty, separate history');
 assert(errors.length===0,errors.join('\n'));report.passed=true;
}catch(error){report.error=String(error);if(page)await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});process.exitCode=1;}
finally{for(const child of children)child.kill();if(browser)await browser.close();await mkdir(output,{recursive:true});await writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,steps:report.steps,error:report.error,output}));}
