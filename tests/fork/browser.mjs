// SPDX-License-Identifier: AGPL-3.0-only
// Host acceptance: original UI/engine, fake Handy, real observer, mocked Ollama.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(new URL('../..',import.meta.url).pathname);
const output=process.env.FORK_BROWSER_REPORT||'/tmp/edgeloop-f2-browser';
const aiSource=process.env.EDGELOOP_AI_SOURCE||'/home/sean/projects/edgeloop-ai';
const token='browser-fixture-token-'+'x'.repeat(32);
const report={passed:false,steps:[],fixture:'mocked Ollama and Handy; no real hardware'};
const children=[];let browser;
const assert=(x,m)=>{if(!x)throw new Error(m);};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitServer(url){for(let i=0;i<50;i++){try{if((await fetch(url)).ok)return;}catch{}await sleep(100);}throw new Error('Local fixture server unavailable: '+url);}
try {
    await mkdir(output,{recursive:true});
    browser=await chromium.launch();
    children.push(spawn('python3',['tools/serve_local.py','8770'],{cwd:root,stdio:'ignore'}));
    children.push(spawn(aiSource+'/.venv/bin/python',['tests/fork/browser_service.py'],{cwd:root,stdio:'ignore',env:{...process.env,PYTHONPATH:root+':'+aiSource}}));
    await waitServer('http://127.0.0.1:8770/');await waitServer('http://127.0.0.1:8768/health');
    const ctx=await browser.newContext();
    await ctx.addInitScript(()=>{
        const denied=()=>Promise.reject(new DOMException('Fake-only test: permission denied','NotFoundError'));
        Object.defineProperty(navigator,'bluetooth',{value:{requestDevice:denied},configurable:true});
        Object.defineProperty(navigator,'serial',{value:{requestPort:denied,getPorts:async()=>[]},configurable:true});
        if(navigator.mediaDevices)navigator.mediaDevices.getUserMedia=denied;
    });
    const page=await ctx.newPage();const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const handy=[];
    await page.route('**/api/handy/v2/**',async route=>{
        const p=new URL(route.request().url()).pathname;handy.push(p);
        await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(p.endsWith('/connected')?{connected:true}:p.endsWith('/info')?{fwVersion:'3.2.3',model:'Handy 1.1'}:{result:0})});
    });
    await page.goto('http://127.0.0.1:8770/',{waitUntil:'load'});
    await page.locator('#ageConfirmBtn').click();
    if(await page.locator('#wizardOverlay').isVisible())await page.locator('#wizardSkipBtn').click();
    await page.locator('#cardBle').click();await page.getByRole('button',{name:/manual simulator/i}).click();
    await page.locator('#modalSimHrSlider').evaluate(el=>{el.value='98';el.dispatchEvent(new Event('input',{bubbles:true}));});
    await page.locator('#modalEngageSimBtn').click();
    if(await page.locator('#modalCloseBtn').isVisible())await page.locator('#modalCloseBtn').click();
    await page.locator('#cardHandy').click();await page.locator('#modalHandyInput').fill('F2-MOCK-KEY');
    await page.locator('#modalHandyConnectBtn').click();await page.waitForTimeout(900);
    await page.locator('#modalCloseBtn').click();await page.locator('#sessionPlayPauseBtn').click();
    await page.waitForFunction(async()=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='RUNNING';});
    report.steps.push('Original simulated session starts before AI');
    await page.locator('#ai-companion').evaluate(el=>{el.open=true;});
    await page.locator('[data-token]').fill(token);await page.locator('[data-connect]').click();
    await page.waitForFunction(()=>document.querySelector('[data-telemetry]').textContent.includes('Authoritative telemetry connected'));
    await page.locator('[data-model] option[value="mira:latest"]').waitFor({state:'attached'});
    await page.locator('[data-model]').selectOption('mira:latest');await page.locator('[data-select]').click();
    await page.waitForFunction(()=>document.querySelector('[data-selected]').textContent.includes('Active: mira:latest'));
    await page.locator('[data-text]').fill('What is the current BPM?');await page.locator('[data-chat]').evaluate(el=>el.requestSubmit());
    await page.waitForFunction(()=>document.querySelector('[data-history]').textContent.includes('98 BPM'));
    let observed=await(await fetch('http://127.0.0.1:8768/fixture/state')).json();
    assert(observed.state.hr===98&&observed.state.status==='RUNNING','Incorrect observed original state');
    assert(!JSON.stringify(observed).includes('F2-MOCK-KEY'),'Credential leak');
    assert(!JSON.stringify(observed).includes('chosenTargetSeconds'),'Hidden target leak');
    assert(observed.read_only,'Tool executor attached');report.steps.push('Contextual user response and redacted authoritative state');
    await page.locator('[data-model]').selectOption('evelyn:latest');await page.locator('[data-select]').click();
    await page.waitForFunction(()=>document.querySelector('[data-selected]').textContent.includes('Active: evelyn:latest'));
    assert(await page.evaluate(async()=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='RUNNING';}),'Model selection changed original session');
    await page.locator('[data-disconnect]').click();children[1].kill();
    const seconds=await page.evaluate(async()=>{const{state}=await import('/src/js/state.js');return state.sessionSeconds;});
    await page.waitForTimeout(1500);
    assert(await page.evaluate(async old=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='RUNNING'&&state.sessionSeconds>old;},seconds),'Backend outage interrupted original clock');
    await page.locator('#sessionStopBtn').click();
    assert(await page.evaluate(async()=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='IDLE'&&state.strokerSpeed===0;}),'Original stop failed');
    assert(handy.includes('/api/handy/v2/hamp/stop'),'Original driver did not stop mocked Handy');
    assert(errors.length===0,errors.join('\n'));report.steps.push('Model switch, backend disconnect and original Stop remain independent');
    await page.screenshot({path:path.join(output,'companion.png'),fullPage:true});report.passed=true;
} catch(error){report.error=String(error);process.exitCode=1;}
finally {
    for(const p of children)p.kill();if(browser)await browser.close();
    await mkdir(output,{recursive:true});await writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
}
