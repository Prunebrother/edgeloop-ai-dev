# SPDX-License-Identifier: AGPL-3.0-only
"""Windows installer, build checks and launcher logic that can be tested on any platform."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load('build_windows', 'tools/windows/build-windows.py')
installer = load('install_windows', 'tools/windows/install_windows.py')
launcher = load('edgeloop_ai_windows', 'tools/windows/edgeloop_ai_windows.py')
serve = load('serve_local', 'tools/serve_local.py')


def test_windows_name_rules():
    assert build.windows_problems(['index.html', 'src/js/app.js']) == []
    assert 'differ only in case' in build.windows_problems(['MANIFEST.json', 'manifest.json'])[0]
    assert build.windows_problems(['docs/con.txt'])
    assert build.windows_problems(['a/b:c.js'])
    assert build.windows_problems(['trailing.'])
    assert build.windows_problems(['x' * 200])


def test_source_manifest_is_renamed_in_the_windows_bundle():
    text = (ROOT / 'tools/windows/build-windows.py').read_text()
    assert "'SOURCE-MANIFEST.json' if name == 'MANIFEST.json'" in text
    # The committed tree itself must stay free of other case collisions.
    names = [str(p.relative_to(ROOT).as_posix()) for p in ROOT.glob('src/**/*')]
    assert build.windows_problems(names) == []


def test_windows_file_version():
    assert build.numeric('v0.6.0-rc1') == '0.6.0.1'
    assert build.numeric('v0.6.0') == '0.6.0.0'


def test_pinned_windows_inputs():
    win = json.loads((ROOT / 'release-inputs.json').read_text())['windows']
    for key in ['python', 'ollama', 'inno_setup']:
        assert len(win[key]['sha256']) == 64 and win[key]['url'].startswith('https://')
    assert win['download_base'].startswith('https://github.com/')
    assert 'colorama==0.4.6' in win['extra_requirements']


def make_tar(files):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w:gz') as archive:
        for name, body in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(body)
            archive.addfile(info, io.BytesIO(body))
    return data.getvalue()


def split(blob, size):
    return [blob[i:i + size] for i in range(0, len(blob), size)]


def test_parts_are_streamed_into_one_extraction(tmp_path):
    files = {'./a.txt': b'alpha' * 1000, './dir/b.bin': os.urandom(50_000)}
    paths = []
    for i, chunk in enumerate(split(make_tar(files), 7_000)):
        path = tmp_path / f'p.part{i:02d}'
        path.write_bytes(chunk)
        paths.append(path)
    incoming = installer.extract(paths, tmp_path / 'v1')
    assert incoming.name == 'v1.incoming'
    assert (incoming / 'dir/b.bin').read_bytes() == files['./dir/b.bin']


def test_extraction_refuses_unsafe_members(tmp_path):
    path = tmp_path / 'evil.part00'
    path.write_bytes(make_tar({'../escape.txt': b'x'}))
    with pytest.raises(tarfile.TarError):
        installer.extract([path], tmp_path / 'v1')
    assert not (tmp_path / 'escape.txt').exists()


class Parts(BaseHTTPRequestHandler):
    blobs, served, fail_once = {}, [], set()

    def log_message(self, *args):
        pass

    def do_GET(self):
        name = self.path.rsplit('/', 1)[-1]
        body = self.blobs[name]
        start = int(self.headers.get('Range', 'bytes=0-')[6:].split('-')[0])
        self.served.append((name, start))
        if name in self.fail_once:
            # Corrupt the first full download so the checksum retry is exercised.
            self.fail_once.discard(name)
            body = b'X' * len(body)
        self.send_response(206 if start else 200)
        self.send_header('Content-Length', str(len(body) - start))
        self.end_headers()
        self.wfile.write(body[start:])


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Parts)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()


def part(name, body):
    return {'name': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}


def test_download_resumes_and_retries_on_bad_checksum(tmp_path, server):
    a, b = os.urandom(3 * installer.CHUNK + 5), os.urandom(1000)
    Parts.blobs, Parts.served, Parts.fail_once = {'a.part00': a, 'b.part01': b}, [], {'b.part01'}
    cache = tmp_path / 'cache'
    cache.mkdir()
    (cache / 'a.part00.partial').write_bytes(a[:installer.CHUNK])  # An interrupted earlier run.
    found = installer.acquire([part('a.part00', a), part('b.part01', b)], server, cache, None)
    assert [p.read_bytes() for p in found] == [a, b]
    assert ('a.part00', installer.CHUNK) in Parts.served
    assert [s for s in Parts.served if s[0] == 'b.part01'] == [('b.part01', 0), ('b.part01', 0)]


def test_offline_parts_next_to_setup_are_used(tmp_path, server):
    body = os.urandom(2000)
    Parts.blobs, Parts.served = {'a.part00': b''}, []
    offline = tmp_path / 'usb'
    offline.mkdir()
    (offline / 'a.part00').write_bytes(body)
    found = installer.acquire([part('a.part00', body)], server, tmp_path / 'cache', offline)
    assert found == [offline / 'a.part00'] and Parts.served == []


def test_new_install_selects_default_model_and_keeps_existing_settings(tmp_path):
    root = tmp_path / 'v1'
    root.mkdir()
    (root / 'release-inputs.json').write_text(json.dumps({'default_model': 'nova:latest'}))
    data = tmp_path / 'data'
    installer.configure(root, data)
    assert json.loads((data / 'selection.json').read_text())['config']['model'] == 'nova:latest'
    (data / 'selection.json').write_text('{"config": {"model": "mine"}}')
    installer.configure(root, data)
    assert 'mine' in (data / 'selection.json').read_text()


def test_launcher_service_plan_is_loopback_and_private(tmp_path):
    paths = launcher.layout(root=tmp_path / 'app', base=tmp_path / 'base')
    plan = launcher.services(paths, root=tmp_path / 'app', env={'PATH': 'x', 'OLLAMA_HOST': '0.0.0.0', 'EDGELOOP_OBSERVER_PORT': '1'})
    names = [s[0] for s in plan]
    assert names == ['ollama', 'observer', 'web']
    ollama, observer, web = (s[2] for s in plan)
    assert ollama['OLLAMA_HOST'] == '127.0.0.1:11435' and ollama['OLLAMA_NO_CLOUD'] == '1'
    assert ollama['OLLAMA_MODELS'] == str(tmp_path / 'app/models')
    assert observer['EDGELOOP_OBSERVER_PORT'] == '8768'
    assert observer['EDGELOOP_FORK_AI_DATA'] == str(tmp_path / 'base/data')
    assert observer['EDGELOOP_PAIRING_FILE'] == web['EDGELOOP_PAIRING_FILE'] == str(tmp_path / 'base/runtime/pairing.json')
    assert all(url.startswith('http://127.0.0.1:') for *_, url, _ in plan)
    assert plan[1][1][1:] == ['-I', '-m', 'ai_observer.server']


def test_launcher_only_stops_the_processes_it_started(tmp_path):
    import psutil
    me = psutil.Process()
    assert launcher.ours({'pid': me.pid, 'created': me.create_time(), 'exe': me.exe()}) is not None
    # A reused PID belongs to a different process: different start time or program.
    assert launcher.ours({'pid': me.pid, 'created': me.create_time() - 100, 'exe': me.exe()}) is None
    assert launcher.ours({'pid': me.pid, 'created': me.create_time(), 'exe': str(tmp_path / 'other.exe')}) is None
    assert launcher.ours({}) is None


def test_windows_home_override(tmp_path):
    assert launcher.base_dir({'EDGELOOP_WINDOWS_HOME': str(tmp_path)}) == tmp_path
    assert launcher.base_dir({'LOCALAPPDATA': str(tmp_path)}) == tmp_path / 'EdgeLoop AI'


@pytest.mark.parametrize('raw', ['/src/js/..%5C..%5C.venv%5Cpyvenv.cfg', '/src/js/app.js::$DATA', '/src/js/C:x.js', '/MANIFEST.json'])
def test_static_server_refuses_windows_path_tricks(raw):
    assert serve.public_file(raw) is None


def test_static_server_still_serves_the_app():
    assert serve.public_file('/src/js/app.js') is not None
    assert serve.public_file('/') is not None
