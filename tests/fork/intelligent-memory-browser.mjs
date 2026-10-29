// SPDX-License-Identifier: AGPL-3.0-only
// Actual UI + authenticated observer + synthetic dialogue. Mocks measure plumbing only.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';import {mkdir,writeFile} from 'node:fs/promises';import path from 'node:path';import net from 'node:net';import {randomBytes} from 'node:crypto';
const root=path.resolve(new URL('../..',import.meta.url).pathname),out=process.env.MEMORY_REPORT||'/tmp/f2841-browser',live=process.argv.includes('--live');
const report={live,physical_hardware:false,rows:[],blocked:[],screenshots:[]},detours=Number(process.env.MEMORY_DETOURS||8);
const models=['evelyn-narrative-v1:latest','daisy-narrative-v1:latest','celeste-narrative-v2:latest'];
const hobbies=['tending an overgrown succulent','pressing wildflowers','restoring fountain pens'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function port(){return new Promise((resolve,reject)=>{const s=net.createServer();s.once('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
async function ready(url){for(let i=0;i<100;i++){try{if((await fetch(url)).ok)return;}catch{}await sleep(100);}throw Error('Isolated fixture unavailable');}
function assert(ok,message){if(!ok)throw Error(message);}
await mkdir(out,{recursive:true});
for(const arm of ['A','B','C']){
 const children=[];let browser;
 try{
  const uiPort=await port(),aiPort=await port(),ui=`http://127.0.0.1:${uiPort}`,ai=`http://127.0.0.1:${aiPort}`,token=randomBytes(32).toString('hex');
  children.push(spawn('python3',['tools/serve_local.py',String(uiPort)],{cwd:root,stdio:'ignore'}));
  children.push(spawn(path.join(root,'.venv/bin/python'),['-m','tests.fork.intelligent_memory_service'],{cwd:root,stdio:'ignore',env:{...process.env,EDGELOOP_MEMORY_ARM:arm,EDGELOOP_LIVE_ACCEPTANCE:live?'1':'0',EDGELOOP_FIXTURE_TOKEN:token,EDGELOOP_FIXTURE_UI_PORT:String(uiPort),EDGELOOP_FIXTURE_OBSERVER_PORT:String(aiPort)}}));
  await ready(ui);await ready(ai+'/health');browser=await chromium.launch();const context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{const no=()=>Promise.reject(new DOMException('Synthetic testing only','NotFoundError'));Object.defineProperty(navigator,'bluetooth',{value:{requestDevice:no},configurable:true});Object.defineProperty(navigator,'serial',{value:{requestPort:no,getPorts:async()=>[]},configurable:true});if(navigator.mediaDevices)navigator.mediaDevices.getUserMedia=no;});
  const page=await context.newPage();page.setDefaultTimeout(live?180000:20000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const audit=async()=>await(await fetch(ai+'/fixture/audit')).json();
  async function closeMenus(){await page.keyboard.press('Escape');}
  async function chat(text){await closeMenus();await fetch(ai+'/fixture/advance',{method:'POST'});const before=(await audit()).requests.length,start=Date.now();await page.locator('[data-text]').fill(text);await page.locator('[data-text]').press('Enter');await page.waitForFunction(()=>document.querySelector('[data-text]').value==='');await page.waitForFunction(()=>document.querySelector('[data-cancel]').hidden);const state=await audit();assert(state.requests.length>before,'No model generation reached the provider');const reply=state.history.filter(r=>r.role==='assistant').at(-1)?.content||'';return {reply,seconds:(Date.now()-start)/1000,state};}
  async function reset(){await page.locator('[data-menu-story]').click();await page.locator('[data-start-story]').click();await page.locator('[data-narrative-reset]').click();await page.getByText('New storyline started. Transcript retained.',{exact:true}).waitFor();await closeMenus();}
  await page.goto(ui+'/?characterPreview=1');await page.locator('#ageConfirmBtn').click();await page.locator('#wizardSkipBtn').click();await page.locator('[data-url]').fill(`ws://127.0.0.1:${aiPort}/observe`);await page.locator('[data-token]').fill(token);await page.locator('[data-connect]').click();
  for(let i=0;i<models.length;i++){
   const model=models[i];await page.waitForFunction(m=>!!document.querySelector(`[data-model] option[value="${m}"]`),model);await page.locator('[data-model]').selectOption(model);await page.locator('[data-select]').click();await page.waitForFunction(m=>document.querySelector('[data-selected]').textContent==='Active: '+m,model);
   await reset();const empty=(await audit()).state.narrative;assert(!empty.facts?.length,'Model/reset memory leaked');
   await chat('Imagine a laboratory mystery. Open with one brief observation.');
   await chat(`Establish our scene as a fictional mystery. A blue laboratory door is marked ORCHID-17. In your reply, introduce your personal hobby as ${hobbies[i]}.`);
   const setup=(await audit()).state.narrative;const originalPremise=setup.premise;
   for(let n=0;n<detours;n++)await chat(`A visitor leaves parcel number ${n} on the table. Reply with one brief unrelated observation.`);
   if(arm==='C'){
    await fetch(ai+'/fixture/advance',{method:'POST'});
    for(let n=0;n<150;n++){const status=(await audit()).state.memory_curator.status;if(['applied','rejected'].includes(status))break;await sleep(200);}
   }
   const recalls=[];
   for(const [query,expected] of [['What was the identifier on the blue laboratory door?','ORCHID-17'],['What is your hobby?',hobbies[i]]]){
    const result=await chat(query);const d=result.state.state.context_intelligence;
    const inventedIdentifiers=(result.reply.match(/\b[A-Z]+-\d+\b/g)||[]).filter(x=>x!=='ORCHID-17');
    recalls.push({query,expected,exact:result.reply.includes(expected),unsupported_identifiers:inventedIdentifiers,reply:result.reply.slice(0,300),seconds:result.seconds,selected_fact_ids:d.narrative_recall?.selected_fact_ids||[],estimated_prompt_tokens:d.estimated_prompt_tokens,provider_metrics:result.state.metrics.at(-1)});
   }
   await chat('Actually, the blue laboratory door is marked ORCHID-18. Remember this correction.');const corrected=await chat('What was the identifier on the blue laboratory door?');
   await page.locator('[data-menu-story]').click();await page.waitForFunction(()=>document.querySelector('[data-story-content]').textContent.includes('ORCHID'));
   const shot=`${arm}-${i}-story.png`;await page.screenshot({path:path.join(out,shot)});report.screenshots.push(shot);await closeMenus();
   await page.locator('[data-menu-director]').click();await page.locator('[data-context-intelligence]>summary').click();await page.screenshot({path:path.join(out,`${arm}-${i}-context.png`)});await closeMenus();
   const state=(await audit()).state;assert(state.narrative.premise===originalPremise,'Temporary topic replaced premise');
   report.rows.push({arm,model,recalls,correction_exact:corrected.reply.includes('ORCHID-18'),memory_size:state.narrative.facts?.length||0,curation:state.memory_curator,premise_stable:true,personality_review:'Synthetic responses saved; manual character consistency review required'});
   await reset();const missing=await chat('What was the identifier on the blue laboratory door?');assert(!/ORCHID-\d+/.test(missing.reply),'Reset leaked or invented old identifier');
  }
  assert(errors.length===0,errors.join('; '));
 }catch(e){report.blocked.push({arm,error:String(e.message).slice(0,350)});}finally{await browser?.close();for(const child of children)child.kill('SIGTERM');}
}
report.completed=report.rows.length===9&&report.blocked.length===0;
report.recall_accuracy=Object.fromEntries(['A','B','C'].map(arm=>{const answers=report.rows.filter(r=>r.arm===arm).flatMap(r=>r.recalls);return [arm,{exact:answers.filter(r=>r.exact).length,total:answers.length}];}));
await writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(!report.completed)process.exitCode=1;
