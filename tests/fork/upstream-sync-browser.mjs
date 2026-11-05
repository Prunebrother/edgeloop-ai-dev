// SPDX-License-Identifier: AGPL-3.0-only
// Upstream-sync regression guard (browser): the companion mounts on the current
// upstream page, every engine play style stays observable, emergency stop is an
// engine stop, and the page never reaches an agent/relay endpoint or real device.
// Fixtures only: simulated heart rate, mocked Handy cloud API, mocked Ollama.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(new URL('../..',import.meta.url).pathname);
const output=process.env.FORK_BROWSER_REPORT||'/tmp/edgeloop-upstream-sync-browser';
const python=process.env.EDGELOOP_TEST_PYTHON||path.join(root,'.venv/bin/python');
const uiPort=process.env.FORK_BROWSER_PORT||'8780',observerPort=process.env.FORK_OBSERVER_PORT||'8788';
const uiUrl='http://127.0.0.1:'+uiPort,observerUrl='http://127.0.0.1:'+observerPort;
const token='browser-fixture-token-'+'x'.repeat(32);
const report={passed:false,steps:[],fixture:'simulated HR, mocked Handy and Ollama; no real hardware'};
const children=[];let browser,page;
const assert=(x,m)=>{if(!x)throw new Error(m);};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function waitServer(url){for(let i=0;i<80;i++){try{if((await fetch(url)).ok)return;}catch{}await sleep(100);}throw new Error('Fixture server unavailable: '+url);}
async function observed(predicate,message,timeout=6000){
    const deadline=Date.now()+timeout;let last;
    do{last=await(await fetch(observerUrl+'/fixture/state')).json();if(predicate(last.state||{},last))return last;await sleep(100);}while(Date.now()<deadline);
    throw new Error(message+': '+JSON.stringify(last.state&&{experience:last.state.experience,status:last.state.status,details:last.state.details}));
}
const engine=fn=>page.evaluate(async source=>{const{state}=await import('/src/js/state.js');return new Function('state','return ('+source+')(state)')(state);},fn.toString());
try {
    await mkdir(output,{recursive:true});
    browser=await chromium.launch();
    children.push(spawn('python3',['tools/serve_local.py',uiPort],{cwd:root,stdio:'ignore'}));
    children.push(spawn(python,['tests/fork/browser_service.py'],{cwd:root,stdio:'ignore',env:{...process.env,EDGELOOP_FIXTURE_UI_PORT:uiPort,EDGELOOP_FIXTURE_OBSERVER_PORT:observerPort}}));
    await waitServer(uiUrl+'/');await waitServer(observerUrl+'/health');
    const ctx=await browser.newContext({viewport:{width:1920,height:1080}});
    await ctx.addInitScript(()=>{
        const denied=()=>Promise.reject(new DOMException('Fixture: no real devices','NotFoundError'));
        Object.defineProperty(navigator,'bluetooth',{value:{requestDevice:denied},configurable:true});
        Object.defineProperty(navigator,'serial',{value:{requestPort:denied,getPorts:async()=>[]},configurable:true});
        if(navigator.mediaDevices)navigator.mediaDevices.getUserMedia=denied;
    });
    page=await ctx.newPage();
    const errors=[],handy=[],external=[],forbidden=[],frames=[];
    page.on('websocket',ws=>ws.on('framesent',event=>{try{const m=JSON.parse(event.payload);if(m.type==='observation')frames.push(m);}catch{}}));
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error'&&!/Failed to load resource/.test(m.text()))errors.push('console: '+m.text());});
    await page.route('**/*',async route=>{
        const url=new URL(route.request().url());
        if(/\/api\/(agent|room)\b/.test(url.pathname))forbidden.push(url.href);
        if(url.hostname.endsWith('handyfeeling.com')){
            handy.push(url.pathname);
            return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(url.pathname.endsWith('/connected')?{connected:true}:url.pathname.endsWith('/info')?{fwVersion:'3.2.3',model:'Handy 1.1'}:{result:0})});
        }
        if(!['127.0.0.1','localhost'].includes(url.hostname)){external.push(url.href);return route.abort();}
        return route.continue();
    });
    await page.goto(uiUrl+'/',{waitUntil:'load'});
    await page.locator('#ageConfirmBtn').click();
    await page.locator('#wizardOverlay').waitFor({state:'visible'});await page.locator('#wizardSkipBtn').click();
    await page.locator('#companion-dashboard').waitFor({timeout:8000}).catch(()=>{throw new Error('Companion did not mount on the upstream page');});
    const missing=await page.evaluate(async()=>{
        const original=new DOMParser().parseFromString(await(await fetch('/index.html')).text(),'text/html');
        return [...original.querySelectorAll('[id]')].map(el=>el.id).filter(id=>!document.getElementById(id));
    });
    assert(!missing.length,'Original elements lost by the companion layout: '+missing.join(', '));
    for(const id of ['sessionStopBtn','sessionPlayPauseBtn','disconnectBanner'])assert(await page.locator('#'+id).count()===1,'Missing engine control '+id);
    assert(await page.locator('#companion-dashboard [data-emergency]').count()===1,'Emergency stop missing from companion');
    await page.setViewportSize({width:390,height:844});
    for(const view of ['session','character','chat']){
        await page.locator(`button[data-view="${view}"]`).click();
        assert(await page.locator('#companion-dashboard').getAttribute('data-view')===view,'View switch failed: '+view);
        if(view==='session')assert(await page.locator('#sessionStopBtn').isVisible(),'Stop not reachable in the Session view');
    }
    await page.setViewportSize({width:1920,height:1080});
    report.steps.push('Companion mounts on the upstream page; every original element and engine control is preserved');

    await page.locator('#cardBle').click();await page.getByRole('button',{name:/manual simulator/i}).click();
    await page.locator('#modalSimHrSlider').evaluate(el=>{el.value='98';el.dispatchEvent(new Event('input',{bubbles:true}));});
    await page.locator('#modalEngageSimBtn').click();
    if(await page.locator('#modalCloseBtn').isVisible())await page.locator('#modalCloseBtn').click();
    await page.locator('[data-url]').fill('ws://127.0.0.1:'+observerPort+'/observe');
    await page.locator('[data-token]').fill(token);await page.locator('[data-connect]').click();
    await page.waitForFunction(()=>document.querySelector('[data-telemetry]').textContent.includes('Authoritative telemetry connected'));
    assert(handy.length===0,'Hardware contacted without a user connection');
    // Every play style the engine offers must project; an unknown one would blind the companion.
    const styles=await page.evaluate(async()=>{const{TEASE_MODES}=await import('/src/js/engine.js');
        return TEASE_MODES.filter(mode=>document.querySelector(`[data-mode="${mode}"]`));});
    const engineStyles=await page.evaluate(async()=>(await import('/src/js/engine.js')).TEASE_MODES);
    for(const mode of styles){
        await page.locator(`[data-mode="${mode}"]`).first().evaluate(el=>el.click());
        assert(await engine(new Function('return state=>state.teaseMode')())===mode,'Engine did not take play style '+mode);
        await observed(s=>s.experience===mode,'Observer did not receive play style '+mode);
    }
    await page.locator('[data-mode="classic"]').first().evaluate(el=>el.click());
    report.steps.push('Observed play styles: '+styles.join(', ')+' (engine: '+engineStyles.join(', ')+')');

    await page.locator('#cardHandy').click();await page.locator('#modalHandyInput').fill('F2-MOCK-KEY');
    await page.locator('#modalHandyConnectBtn').click();await page.waitForTimeout(900);
    if(await page.locator('#modalCloseBtn').isVisible())await page.locator('#modalCloseBtn').click();
    await page.locator('#sessionPlayPauseBtn').evaluate(el=>el.click());
    await page.waitForFunction(async()=>{const{state}=await import('/src/js/state.js');return state.sessionStatus==='RUNNING';});
    await observed(s=>s.status==='RUNNING','Observer did not see the session start');
    const before=handy.length;
    await page.locator('#companion-dashboard [data-emergency]').click();
    const after=await engine(new Function('return state=>({status:state.sessionStatus,primary:state.strokerSpeed,secondary:state.prostateSpeed})')());
    assert(after.status==='IDLE'&&after.primary===0&&after.secondary===0,'Emergency stop did not stop the engine: '+JSON.stringify(after));
    await page.waitForTimeout(300);
    assert(handy.slice(before).some(p=>p.endsWith('/hamp/stop')),'Engine driver did not stop the mocked Handy');
    const deadline=Date.now()+4000;
    while(Date.now()<deadline&&!frames.some(f=>f.snapshot?.details?.terminal_outcome==='safety_stop'))await sleep(100);
    const stopFrame=frames.find(f=>f.snapshot?.details?.terminal_outcome==='safety_stop');
    assert(stopFrame&&stopFrame.snapshot.status==='IDLE'&&stopFrame.snapshot.movement.primary===0,'Observer was not sent a safety_stop projection');
    assert(stopFrame.events?.some(e=>e.kind==='stop'),'Safety stop projection carried no stop event');
    report.steps.push('Emergency stop is an engine stop: motors zero, mocked Handy stopped, observer records safety_stop');

    assert(!forbidden.length,'Agent/relay endpoint contacted: '+forbidden.join(', '));
    assert(!errors.length,'Page errors: '+errors.join('\n'));
    report.steps.push('No agent/relay requests; external requests blocked: '+[...new Set(external.map(u=>new URL(u).hostname))].join(', '));
    await page.screenshot({path:path.join(output,'upstream-sync.png'),fullPage:true});
    report.passed=true;
} catch(error){report.error=String(error);if(page)await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});process.exitCode=1;}
finally {
    for(const p of children)p.kill();if(browser)await browser.close();
    await mkdir(output,{recursive:true});await writeFile(path.join(output,'report.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
}
