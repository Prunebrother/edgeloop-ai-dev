import { describe, it, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import net from 'node:net';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createAppHost, scanLibrary, publicFile } from './host.mjs';
import { encodePacket } from '../src/js/player/sync-protocol.js';

function readSync(url) {
    return new Promise((resolve, reject) => {
        const req = http.get(url, (res) => {
            let buf = '';
            const timer = setTimeout(() => {
                req.destroy();
                reject(new Error('no sync'));
            }, 3000);
            res.on('data', (chunk) => {
                buf += chunk.toString('utf8');
                const parts = buf.split('\n\n');
                buf = parts.pop() || '';
                for (const part of parts) {
                    const line = part.split('\n').find((item) => item.startsWith('data: '));
                    if (!line) continue;
                    const data = JSON.parse(line.slice(6));
                    if (data.connected && data.stroke && data.stroke.name === 'Scene.funscript' && data.mediaMs >= 4000) {
                        clearTimeout(timer);
                        req.destroy();
                        resolve(data);
                    }
                }
            });
        });
        req.on('error', (err) => {
            if (err.code !== 'ECONNRESET') reject(err);
        });
    });
}

describe('local app host', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'el-app-'));
    fs.writeFileSync(path.join(dir, 'Scene.funscript'), '{"actions":[{"at":0,"pos":0},{"at":1000,"pos":100}]}');
    fs.writeFileSync(path.join(dir, 'Scene.v0.funscript'), '{"actions":[{"at":0,"pos":10},{"at":1000,"pos":20}]}');
    const statePath = path.join(dir, 'state.json');
    let host;
    let headset;

    after(async () => {
        if (host) await host.close();
        if (headset) headset.close();
        fs.rmSync(dir, { recursive: true, force: true });
    });

    it('scans a folder and keeps only videos and scripts', () => {
        fs.writeFileSync(path.join(dir, 'notes.txt'), 'nope');
        const found = scanLibrary(dir);
        const names = found.files.map((file) => file.name).sort();
        assert.deepEqual(names, ['Scene.funscript', 'Scene.v0.funscript']);
    });

    it('follows a headset timestamp server and names the matching script', async () => {
        headset = net.createServer((socket) => {
            socket.write(encodePacket({
                path: '/storage/Movies/Scene.mp4',
                duration: 30,
                currentTime: 4,
                playbackSpeed: 1,
                playerState: 0
            }));
            socket.on('data', () => {});
        });
        await new Promise((resolve) => headset.listen(0, '127.0.0.1', resolve));
        const headsetPort = headset.address().port;
        host = await createAppHost({ port: 0, openBrowser: false, statePath });
        // What the page sends: same Origin, the custom header and JSON.
        const page = { 'Content-Type': 'application/json', 'X-EdgeLoop-App': '1', Origin: host.url.replace(/\/$/, '') };
        const library = await fetch(host.url + 'app/library', {
            method: 'POST',
            headers: page,
            body: JSON.stringify({ path: dir })
        });
        assert.equal((await library.json()).ok, true);
        const connect = await fetch(host.url + 'app/connect', {
            method: 'POST',
            headers: page,
            body: JSON.stringify({ host: '127.0.0.1', port: headsetPort })
        });
        assert.equal((await connect.json()).ok, true);
        const seen = await readSync(host.url + 'app/events');
        assert.equal(seen.vib.name, 'Scene.v0.funscript');
        assert.equal(seen.state, 'playing');
        assert.equal(seen.source, 'headset');
        const script = await fetch(host.url + 'app/script?id=' + encodeURIComponent(seen.stroke.id));
        const body = await script.json();
        assert.equal(body.name, 'Scene.funscript');
        assert.match(body.text, /actions/);
    });

    it('serves only public files: no private data, sibling directories or symlink escapes', async () => {
        const base = fs.mkdtempSync(path.join(os.tmpdir(), 'edgeloop-host-files-'));
        const root = path.join(base, 'public'), sibling = path.join(base, 'public-private');
        fs.mkdirSync(path.join(root, '.ai-data'), { recursive: true });
        fs.mkdirSync(path.join(root, 'src/js'), { recursive: true });
        fs.mkdirSync(path.join(root, 'app'), { recursive: true });
        fs.mkdirSync(sibling);
        fs.writeFileSync(path.join(root, 'index.html'), 'page');
        fs.writeFileSync(path.join(root, 'src/js/app.js'), 'code');
        fs.writeFileSync(path.join(root, '.ai-data/selection.json'), 'PRIVATE');
        fs.writeFileSync(path.join(root, 'app/app-state.json'), '{"vlcPassword":"x"}');
        fs.writeFileSync(path.join(sibling, 'secret.txt'), 'OUTSIDE');
        fs.writeFileSync(path.join(sibling, 'evil.js'), 'OUTSIDE');
        fs.symlinkSync(path.join(sibling, 'evil.js'), path.join(root, 'src/js/linked.js'));
        const local = await createAppHost({ port: 0, root, statePath: path.join(base, 'state.json') });
        try {
            const get = async (p, headers = {}) => { const r = await fetch(local.url.replace(/\/$/, '') + p, { headers }); return [r.status, await r.text()]; };
            assert.deepEqual(await get('/'), [200, 'page']);
            assert.deepEqual(await get('/src/js/app.js'), [200, 'code']);
            for (const p of ['/.ai-data/selection.json', '/%2eai-data/selection.json', '/app/app-state.json', '/..%2fpublic-private/secret.txt',
                '/src/js/..%2f..%2f..%2fpublic-private/evil.js', '/src/js/linked.js', '/.git/config', '/src%5cjs%5capp.js']) {
                const [status, body] = await get(p);
                assert.equal(status, 404, p);
                assert.ok(!/PRIVATE|OUTSIDE|vlcPassword/.test(body), p);
            }
            assert.equal(publicFile('/src/js/linked.js', root), null);
        } finally {
            await local.close();
            fs.rmSync(base, { recursive: true, force: true });
        }
    });

    it('refuses foreign Host and Origin values and unmarked state changes', async () => {
        const base = fs.mkdtempSync(path.join(os.tmpdir(), 'edgeloop-host-origin-'));
        fs.writeFileSync(path.join(base, 'index.html'), 'page');
        let quits = 0;
        const local = await createAppHost({ port: 0, root: base, statePath: path.join(base, 'state.json'), onQuit: () => { quits++; } });
        const own = `127.0.0.1:${local.port}`;
        const send = (method, p, headers) => new Promise((resolve, reject) => {
            const req = http.request({ host: '127.0.0.1', port: local.port, path: p, method, headers }, (res) => { res.resume(); res.on('end', () => resolve(res.statusCode)); });
            req.on('error', reject); req.end(method === 'POST' && headers['Content-Type'] ? '{}' : undefined);
        });
        try {
            assert.equal(await send('GET', '/', { Host: 'attacker.invalid' }), 403);
            assert.equal(await send('GET', '/', { Host: own, Origin: 'http://attacker.invalid' }), 403);
            assert.equal(await send('GET', '/', { Host: own }), 200);
            assert.equal(await send('POST', '/app/quit', { Host: own, Origin: 'http://attacker.invalid', 'Content-Type': 'text/plain', 'X-EdgeLoop-App': '1' }), 403);
            assert.equal(await send('POST', '/app/quit', { Host: own, Origin: 'http://' + own }), 403);
            assert.equal(await send('POST', '/app/quit', { Host: own, 'X-EdgeLoop-App': '1' }), 403);
            assert.equal(await send('POST', '/app/disconnect', { Host: 'attacker.invalid:' + local.port, Origin: 'http://attacker.invalid:' + local.port, 'X-EdgeLoop-App': '1' }), 403);
            assert.equal(await send('POST', '/app/library', { Host: own, Origin: 'http://' + own, 'X-EdgeLoop-App': '1', 'Content-Type': 'text/plain' }), 415);
            await new Promise((resolve) => setImmediate(resolve));
            assert.equal(quits, 0);
            assert.equal(await send('POST', '/app/quit', { Host: own, Origin: 'http://' + own, 'X-EdgeLoop-App': '1' }), 200);
            await new Promise((resolve) => setImmediate(resolve));
            assert.equal(quits, 1);
        } finally {
            await local.close();
            fs.rmSync(base, { recursive: true, force: true });
        }
    });
});
