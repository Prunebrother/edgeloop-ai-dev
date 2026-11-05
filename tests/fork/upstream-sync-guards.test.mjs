// SPDX-License-Identifier: AGPL-3.0-only
// Regression guards for upstream integration: the AI layer stays a read-only
// observer, the deterministic engine keeps sole control of hardware, and no
// agent command channel arrives silently with an upstream sync.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import path from 'node:path';

const root=path.resolve(new URL('../..',import.meta.url).pathname);
const read=name=>readFileSync(path.join(root,name),'utf8');
const aiFiles=readdirSync(path.join(root,'src/js/ai')).filter(f=>f.endsWith('.js')).map(f=>'src/js/ai/'+f);

test('AI modules import only AI modules and the character manifest, never engine, drivers or transports',()=>{
    for(const file of aiFiles){
        const source=read(file);
        const specifiers=[...source.matchAll(/(?:^|\n)\s*import\s[^;]*?from\s*'([^']+)'|import\(\s*'([^']+)'\s*\)/g)].map(m=>m[1]||m[2]);
        for(const spec of specifiers){
            const allowed=/^\.\/[a-z-]+\.js$/.test(spec)||/^\.\.\/\.\.\/assets\/characters\/manifest\.json(\?[\w=-]+)?$/.test(spec);
            assert.ok(allowed,`${file} imports ${spec}`);
        }
    }
});

test('AI modules contain no hardware, peer, session-command or agent primitives',()=>{
    const forbidden=[/dispatchHardware/,/sendPeerCommand/,/sendControllerCommand/,/navigator\.(bluetooth|serial|usb|hid)/,
        /handyfeeling/i,/\/api\/handy/,/:12345\b/,/buttplug/i,/agent-api/,/\/api\/agent/,/\/api\/room/,
        /SESSION_STATE|MODE_CHANGE|ORGASM_TOGGLE|MANUAL_PATTERN|EDGE_MARK|INTENSITY_CHANGE/];
    for(const file of aiFiles){
        const source=read(file);
        for(const pattern of forbidden)assert.ok(!pattern.test(source),`${file} matches ${pattern}`);
    }
});

test('the only control the AI layer can press is the user-clicked emergency stop',()=>{
    const clicks=aiFiles.flatMap(file=>[...read(file).matchAll(/\.click\(\)/g)].map(()=>file));
    assert.deepEqual(clicks,['src/js/ai/layout.js']);
    const layout=read('src/js/ai/layout.js');
    assert.match(layout,/\[data-emergency\]'\)\.onclick=\(\)=>\{const stop=document\.getElementById\('sessionStopBtn'\);stop\.dataset\.safetyStop='true';stop\.click\(\);\}/);
});

test('the engine mounts the companion with a refresh callback only and keeps its own stop authority',()=>{
    const app=read('src/js/app.js');
    const mounts=[...app.matchAll(/mountCompanion\(([^)]*)\)/g)].map(m=>m[1].trim());
    assert.deepEqual(mounts,['{refreshObservation: syncAiObservation}']);
    // The AI observation is wrapped so a failing projection can never alter the control path.
    assert.match(app,/function syncAiObservation[\s\S]*?try \{[\s\S]*?\} catch \{ \/\* AI is optional/);
    // Emergency stop is an ordinary engine stop with a distinct outcome label.
    assert.match(app,/const safetyStop = stopBtn\.dataset\.safetyStop === 'true';\s*delete stopBtn\.dataset\.safetyStop;\s*stopSession\(safetyStop \? "Emergency Stop" : "Stopped"\);/);
    const stop=app.slice(app.indexOf('function stopSession('));
    const body=stop.slice(0,stop.indexOf('\n}\n'));
    assert.ok(body.indexOf('dispatchHardware(0')>=0,'stopSession no longer zeroes hardware');
    assert.ok(body.indexOf('dispatchHardware(0')<body.indexOf('syncAiObservation'),'AI is notified before motors stop');
});

test('no agent command link is present in this build (see docs/fork/dev/AGENT_LINK_BOUNDARY.md)',()=>{
    assert.ok(!existsSync(path.join(root,'src/js/agent-api.js')),'agent-api.js arrived with a sync');
    assert.ok(!existsSync(path.join(root,'worker')),'Cloudflare worker arrived with a sync');
    assert.ok(!existsSync(path.join(root,'tools/edgeloop_openwebui.py')),'Open WebUI control tool arrived with a sync');
    for(const file of ['src/js/app.js','index.html','sw.js'])
        assert.ok(!/\/api\/agent|agentHttpToken|AgentRoom/.test(read(file)),`${file} contains agent link code`);
});

test('the service worker never caches AI, observer or loopback traffic',()=>{
    const sw=read('sw.js');
    assert.match(sw,/port === '8768' \|\| new URL\(request\.url\)\.pathname\.startsWith\('\/ai\/'\)\) return;/);
    assert.match(sw,/url\.origin !== self\.location\.origin && \['127\.0\.0\.1','localhost','\[::1\]'\]\.includes\(url\.hostname\)\) return;/);
    assert.match(sw,/pathname\.startsWith\('\/Character_Art\/'\)\) return;/);
});
